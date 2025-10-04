# Import numpy and OpenCV
import numpy as np
import cv2
import os
import time


def movingAverage(curve, radius): 
  window_size = 2 * radius + 1
  # Define the filter 
  f = np.ones(window_size)/window_size 
  # Add padding to the boundaries 
  curve_pad = np.lib.pad(curve, (radius, radius), 'edge') 
  # Apply convolution 
  curve_smoothed = np.convolve(curve_pad, f, mode='same') 
  # Remove padding 
  curve_smoothed = curve_smoothed[radius:-radius]
  # return smoothed curve
  return curve_smoothed

def gaussianSmooth(curve, radius):
  """Gaussian smoothing for better stability"""
  window_size = 2 * radius + 1
  # Create gaussian kernel
  sigma = window_size / 6.0  # 3-sigma rule
  x = np.arange(window_size) - radius
  gaussian_kernel = np.exp(-(x**2) / (2 * sigma**2))
  gaussian_kernel = gaussian_kernel / np.sum(gaussian_kernel)
  
  # Add padding to the boundaries 
  curve_pad = np.lib.pad(curve, (radius, radius), 'edge') 
  # Apply convolution 
  curve_smoothed = np.convolve(curve_pad, gaussian_kernel, mode='same') 
  # Remove padding 
  curve_smoothed = curve_smoothed[radius:-radius]
  return curve_smoothed 

def smooth(trajectory): 
  smoothed_trajectory = np.copy(trajectory) 
  # Filter the x, y and angle curves
  for i in range(3):
    if SMOOTHING_METHOD == 'gaussian':
      smoothed_trajectory[:,i] = gaussianSmooth(trajectory[:,i], radius=SMOOTHING_RADIUS)
    else:
      smoothed_trajectory[:,i] = movingAverage(trajectory[:,i], radius=SMOOTHING_RADIUS)

  return smoothed_trajectory

def fixBorder(frame):
  s = frame.shape
  # Scale the image 4% without moving the center
  T = cv2.getRotationMatrix2D((s[1]/2, s[0]/2), 0, 1.04)
  frame = cv2.warpAffine(frame, T, (s[1], s[0]))
  return frame

def drawFPS(frame, fps, position):
  """Draw FPS information on frame"""
  fps_text = f"FPS: {fps:.1f}"
  
  # Create background rectangle for better visibility
  font = cv2.FONT_HERSHEY_SIMPLEX
  font_scale = 0.7
  thickness = 2
  
  # Get text size
  (text_width, text_height), baseline = cv2.getTextSize(fps_text, font, font_scale, thickness)
  
  # Draw background rectangle
  cv2.rectangle(frame, 
                (position[0] - 5, position[1] - text_height - 5),
                (position[0] + text_width + 5, position[1] + baseline + 5),
                (0, 0, 0), -1)
  
  # Draw FPS text
  cv2.putText(frame, fps_text, position, font, font_scale, (0, 255, 0), thickness)
  
  return frame


# The larger the more stable the video, but less reactive to sudden panning
# Increased from 50 to 100 for better stability
SMOOTHING_RADIUS=50

# Smoothing method: 'moving_average' or 'gaussian'
# Gaussian provides smoother results but may be less responsive
SMOOTHING_METHOD = 'gaussian'  # Change to 'moving_average' if needed

# Apply double smoothing for extra stability (set to True for maximum stability)
DOUBLE_SMOOTHING = True

# FPS display settings
SHOW_FPS = True  # Set to False to hide FPS
FPS_POSITION = (10, 30)  # (x, y) position for FPS text 

# Read input video
cap = cv2.VideoCapture(r'C:\Users\TOM\Documents\Projeler\AybuHavk\GoruntuStabilize\deneme.mp4') 
 
# Get frame count
n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) 
 
# Get width and height of video stream
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) 
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Get frames per second (fps)
fps = cap.get(cv2.CAP_PROP_FPS)
 
# Define the codec for output video - try multiple codecs for better compatibility
codecs_to_try = ['mp4v', 'XVID', 'MJPG', 'H264']
fourcc = None
out = None

# Set up output video with proper dimensions
output_width = 2 * w
output_height = h

# Try different codecs until one works
for codec in codecs_to_try:
    try:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter('video_out.mp4', fourcc, fps, (output_width, output_height))
        if out.isOpened():
            print(f"Successfully initialized video writer with codec: {codec}")
            break
        else:
            out.release()
            out = None
    except:
        continue

# Check if VideoWriter was initialized successfully
if out is None or not out.isOpened():
    print("Error: Could not open video writer with any codec")
    print("Tried codecs:", codecs_to_try)
    exit()

# Read first frame
_, prev = cap.read() 
 
# Convert frame to grayscale
prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY) 

# Pre-define transformation-store array
transforms = np.zeros((n_frames-1, 3), np.float32) 

for i in range(n_frames-2):
  # Detect feature points in previous frame
  prev_pts = cv2.goodFeaturesToTrack(prev_gray,
                                     maxCorners=200,
                                     qualityLevel=0.01,
                                     minDistance=30,
                                     blockSize=3)
   
  # Read next frame
  success, curr = cap.read() 
  if not success: 
    break 

  # Convert to grayscale
  curr_gray = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY) 

  # If no features found, skip to next frame
  if prev_pts is None:
    prev_gray = curr_gray
    print("Frame: " + str(i) + "/" + str(n_frames) + " -  Tracked points : 0 (no features)")
    continue

  # Calculate optical flow (i.e. track feature points)
  curr_pts, status, err = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None) 

  # Sanity check
  assert prev_pts.shape == curr_pts.shape 

  # Filter only valid points
  idx = np.where(status==1)[0]
  prev_pts = prev_pts[idx]
  curr_pts = curr_pts[idx]

  # Find transformation matrix using OpenCV 4+ API
  # estimateAffinePartial2D expects shape (N,2)
  prev_pts_2d = prev_pts.reshape(-1, 2)
  curr_pts_2d = curr_pts.reshape(-1, 2)
  m, inliers = cv2.estimateAffinePartial2D(prev_pts_2d, curr_pts_2d)
  # Fallback to identity if estimation fails
  if m is None:
    m = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
   
  # Extract traslation
  dx = m[0,2]
  dy = m[1,2]

  # Extract rotation angle
  da = np.arctan2(m[1,0], m[0,0])
   
  # Store transformation
  transforms[i] = [dx,dy,da]
   
  # Move to next frame
  prev_gray = curr_gray

  print("Frame: " + str(i) +  "/" + str(n_frames) + " -  Tracked points : " + str(len(prev_pts)))

# Compute trajectory using cumulative sum of transformations
trajectory = np.cumsum(transforms, axis=0) 
 
# Create variable to store smoothed trajectory
smoothed_trajectory = smooth(trajectory)

# Apply double smoothing for extra stability if enabled
if DOUBLE_SMOOTHING:
    print("Applying double smoothing for maximum stability...")
    smoothed_trajectory = smooth(smoothed_trajectory) 

# Calculate difference in smoothed_trajectory and trajectory
difference = smoothed_trajectory - trajectory
 
# Calculate newer transformation array
transforms_smooth = transforms + difference

# Reset stream to first frame 
cap.set(cv2.CAP_PROP_POS_FRAMES, 0) 

# FPS calculation variables
fps_start_time = time.time()
frame_count = 0

# Write n_frames-1 transformed frames
for i in range(n_frames-2):
  # Read next frame
  success, frame = cap.read() 
  if not success:
    break

  # Extract transformations from the new transformation array
  dx = transforms_smooth[i,0]
  dy = transforms_smooth[i,1]
  da = transforms_smooth[i,2]

  # Reconstruct transformation matrix accordingly to new values
  m = np.zeros((2,3), np.float32)
  m[0,0] = np.cos(da)
  m[0,1] = -np.sin(da)
  m[1,0] = np.sin(da)
  m[1,1] = np.cos(da)
  m[0,2] = dx
  m[1,2] = dy

  # Apply affine wrapping to the given frame
  frame_stabilized = cv2.warpAffine(frame, m, (w,h))

  # Fix border artifacts
  frame_stabilized = fixBorder(frame_stabilized) 

  # Write the frame to the file
  frame_out = cv2.hconcat([frame, frame_stabilized])

  # If the image is too big, resize it.
  if(frame_out.shape[1] > 1920): 
    frame_out = cv2.resize(frame_out, (frame_out.shape[1]//2, frame_out.shape[0]//2));
  
  # Ensure frame dimensions match VideoWriter expectations
  if frame_out.shape[:2] != (output_height, output_width):
    frame_out = cv2.resize(frame_out, (output_width, output_height))
  
  # Calculate and display FPS
  if SHOW_FPS:
    frame_count += 1
    current_time = time.time()
    elapsed_time = current_time - fps_start_time
    
    if elapsed_time > 0:
      current_fps = frame_count / elapsed_time
      frame_out = drawFPS(frame_out, current_fps, FPS_POSITION)
  
  cv2.imshow("Before and After", frame_out)
  cv2.waitKey(10)
  
  # Write frame with error checking
  success = out.write(frame_out)
  if not success:
    print(f"Warning: Failed to write frame {i}")

# Release video and ensure proper cleanup
cap.release()

# Ensure all frames are written before releasing
out.release()

# Calculate and display final FPS statistics
if SHOW_FPS:
    total_time = time.time() - fps_start_time
    average_fps = frame_count / total_time if total_time > 0 else 0
    print(f"\n=== FPS Statistics ===")
    print(f"Total frames processed: {frame_count}")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Average FPS: {average_fps:.2f}")

# Verify video file was created successfully
if os.path.exists('video_out.mp4'):
    file_size = os.path.getsize('video_out.mp4')
    if file_size > 0:
        print(f"Video successfully saved as 'video_out.mp4' ({file_size} bytes)")
    else:
        print("Warning: Video file is empty")
else:
    print("Error: Video file was not created")

# Close windows
cv2.destroyAllWindows()