""" 
        
        Şuan da bu kod doğru çalışmıyor. 


"""
import cv2
import numpy as np
from collections import deque
import time


class KalmanFilter:
    """Kalman Filtresi - Hareket tahmini ve düzeltme için"""
    
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.x = 0.0  # Durum tahmini
        self.P = 1.0  # Hata kovaryansı
        self.Q = process_noise  # Süreç gürültüsü
        self.R = measurement_noise  # Ölçüm gürültüsü
        
    def update(self, measurement):
        # Tahmin adımı
        x_pred = self.x
        P_pred = self.P + self.Q
        
        # Güncelleme adımı
        K = P_pred / (P_pred + self.R)  # Kalman kazancı
        self.x = x_pred + K * (measurement - x_pred)
        self.P = (1 - K) * P_pred
        
        return self.x


class ImageStabilizer:
    """Görüntü Stabilizasyon Sınıfı"""
    
    def __init__(self, smoothing_factor=0.8):
        self.smoothing_factor = smoothing_factor
        
        # Kalman filtreleri
        self.kalman_x = KalmanFilter(process_noise=0.01, measurement_noise=0.1)
        self.kalman_y = KalmanFilter(process_noise=0.01, measurement_noise=0.1)
        self.kalman_angle = KalmanFilter(process_noise=0.001, measurement_noise=0.01)
        
        # Transformasyon parametreleri
        self.cumulative_transform = {'x': 0.0, 'y': 0.0, 'angle': 0.0}
        self.smoothed_transform = {'x': 0.0, 'y': 0.0, 'angle': 0.0}
        
        # Önceki frame
        self.prev_gray = None
        self.prev_points = None
        
        # Optik akış parametreleri
        self.feature_params = dict(
            maxCorners=200,
            qualityLevel=0.01,
            minDistance=30,
            blockSize=7
        )
        
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
        # İstatistikler
        self.motion_history = deque(maxlen=30)
        self.fps_history = deque(maxlen=30)
        
    def detect_features(self, gray):
        """Özellik noktalarını tespit et"""
        points = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
        return points
    
    def calculate_motion(self, prev_gray, curr_gray, prev_points):
        """Optik akış ile hareket hesapla"""
        if prev_points is None or len(prev_points) == 0:
            return None, None
        
        # Lucas-Kanade optik akış
        curr_points, status, error = cv2.calcOpticalFlowPyrLK(
            prev_gray, curr_gray, prev_points, None, **self.lk_params
        )
        
        if curr_points is None:
            return None, None
        
        # Sadece başarılı eşleşmeleri kullan
        idx = np.where(status == 1)[0]
        prev_pts = prev_points[idx]
        curr_pts = curr_points[idx]
        
        if len(prev_pts) < 5:
            return None, None
        
        # Affine transformasyon matrisini hesapla
        try:
            transform_matrix, inliers = cv2.estimateAffinePartial2D(
                prev_pts, curr_pts, method=cv2.RANSAC, ransacReprojThreshold=3.0
            )
            
            if transform_matrix is None:
                return None, None
            
            # Transformasyon parametrelerini çıkar
            dx = transform_matrix[0, 2]
            dy = transform_matrix[1, 2]
            da = np.arctan2(transform_matrix[1, 0], transform_matrix[0, 0])
            
            return {'x': dx, 'y': dy, 'angle': da}, curr_pts[inliers.ravel() == 1]
            
        except Exception as e:
            print(f"Transform hesaplama hatası: {e}")
            return None, None
    
    def apply_stabilization(self, frame, motion):
        """Stabilizasyon uygula"""
        h, w = frame.shape[:2]
        
        if motion is None:
            return frame, 0.0
        
        # Kümülatif transformasyonu güncelle
        self.cumulative_transform['x'] += motion['x']
        self.cumulative_transform['y'] += motion['y']
        self.cumulative_transform['angle'] += motion['angle']
        
        # Kalman filtresi ile düzelt
        smooth_x = self.kalman_x.update(self.cumulative_transform['x'])
        smooth_y = self.kalman_y.update(self.cumulative_transform['y'])
        smooth_angle = self.kalman_angle.update(self.cumulative_transform['angle'])
        
        # Yumuşatılmış transformasyonu güncelle
        alpha = self.smoothing_factor
        self.smoothed_transform['x'] = (
            alpha * self.smoothed_transform['x'] + (1 - alpha) * smooth_x
        )
        self.smoothed_transform['y'] = (
            alpha * self.smoothed_transform['y'] + (1 - alpha) * smooth_y
        )
        self.smoothed_transform['angle'] = (
            alpha * self.smoothed_transform['angle'] + (1 - alpha) * smooth_angle
        )
        
        # Kompenzasyon hesapla
        dx = self.cumulative_transform['x'] - self.smoothed_transform['x']
        dy = self.cumulative_transform['y'] - self.smoothed_transform['y']
        da = self.cumulative_transform['angle'] - self.smoothed_transform['angle']
        
        # Hareket büyüklüğü
        motion_magnitude = np.sqrt(dx**2 + dy**2)
        
        # Transformasyon matrisini oluştur
        transform_matrix = np.array([
            [np.cos(da), -np.sin(da), dx],
            [np.sin(da), np.cos(da), dy]
        ], dtype=np.float32)
        
        # Görüntüyü transforme et
        stabilized = cv2.warpAffine(
            frame, transform_matrix, (w, h),
            borderMode=cv2.BORDER_REFLECT_101
        )
        
        # Crop (kenarları kırp)
        crop_margin = int(min(w, h) * 0.05)
        stabilized = stabilized[
            crop_margin:h-crop_margin,
            crop_margin:w-crop_margin
        ]
        stabilized = cv2.resize(stabilized, (w, h))
        
        return stabilized, motion_magnitude
    
    def process_frame(self, frame):
        """Frame işle"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            self.prev_points = self.detect_features(gray)
            return frame, 0.0
        
        # Hareket hesapla
        motion, curr_points = self.calculate_motion(
            self.prev_gray, gray, self.prev_points
        )
        
        # Stabilizasyon uygula
        stabilized_frame, motion_magnitude = self.apply_stabilization(frame, motion)
        
        # Yeni özellik noktaları tespit et
        if curr_points is None or len(curr_points) < 50:
            self.prev_points = self.detect_features(gray)
        else:
            self.prev_points = curr_points.reshape(-1, 1, 2)
        
        self.prev_gray = gray
        self.motion_history.append(motion_magnitude)
        
        return stabilized_frame, motion_magnitude
    
    def reset(self):
        """Stabilizatörü sıfırla"""
        self.kalman_x = KalmanFilter()
        self.kalman_y = KalmanFilter()
        self.kalman_angle = KalmanFilter()
        self.cumulative_transform = {'x': 0.0, 'y': 0.0, 'angle': 0.0}
        self.smoothed_transform = {'x': 0.0, 'y': 0.0, 'angle': 0.0}
        self.prev_gray = None
        self.prev_points = None


def add_info_overlay(frame, fps, motion, stabilization_enabled):
    """Bilgi overlay'i ekle"""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    
    # Yarı saydam panel
    cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
    
    # Bilgileri yaz
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Motion: {motion:.2f} px", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    status = "ON" if stabilization_enabled else "OFF"
    color = (0, 255, 0) if stabilization_enabled else (0, 0, 255)
    cv2.putText(frame, f"Stabilization: {status}", (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    return frame


def main():
    """Ana program"""
    print("=" * 60)
    print("GÖRÜNTÜ STABİLİZASYON SİSTEMİ")
    print("=" * 60)
    print("\nKaynak seçin:")
    print("1. Kamera (Webcam)")
    print("2. Video dosyası")
    
    choice = input("\nSeçiminiz (1/2): ").strip()
    
    # Video kaynağını aç
    if choice == '1':
        cap = cv2.VideoCapture(2)
        print("\n✓ Kamera açılıyor...")
    else:
        video_path = input("Video dosyası yolu: ").strip()
        cap = cv2.VideoCapture(video_path)
        print(f"\n✓ Video yükleniyor: {video_path}")
    
    if not cap.isOpened():
        print("✗ Hata: Video kaynağı açılamadı!")
        return
    
    # Stabilizatörü oluştur
    stabilizer = ImageStabilizer(smoothing_factor=0.8)
    
    # Değişkenler
    stabilization_enabled = True
    fps_list = deque(maxlen=30)
    
    print("\n" + "=" * 60)
    print("KONTROLLER:")
    print("  [SPACE] - Stabilizasyonu Aç/Kapat")
    print("  [R]     - Stabilizatörü Sıfırla")
    print("  [+/-]   - Yumuşatma Faktörünü Ayarla")
    print("  [Q/ESC] - Çıkış")
    print("=" * 60 + "\n")
    
    while True:
        start_time = time.time()
        
        ret, frame = cap.read()
        if not ret:
            print("\n✗ Frame okunamadı veya video bitti!")
            break
        
        # Frame'i yeniden boyutlandır
        frame = cv2.resize(frame, (640, 480))
        
        # Stabilizasyon işle
        if stabilization_enabled:
            stabilized_frame, motion = stabilizer.process_frame(frame.copy())
        else:
            stabilized_frame = frame.copy()
            motion = 0.0
        
        # FPS hesapla
        elapsed = time.time() - start_time
        fps = 1.0 / elapsed if elapsed > 0 else 0
        fps_list.append(fps)
        avg_fps = np.mean(fps_list)
        
        # Bilgi overlay'i ekle
        frame_with_info = add_info_overlay(frame, avg_fps, motion, False)
        stabilized_with_info = add_info_overlay(
            stabilized_frame, avg_fps, motion, stabilization_enabled
        )
        
        # Yan yana göster
        combined = np.hstack([frame_with_info, stabilized_with_info])
        
        # Etiketler ekle
        cv2.putText(combined, "ORIGINAL", (10, combined.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(combined, "STABILIZED", (650, combined.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.imshow('Image Stabilization System', combined)
        
        # Klavye kontrolleri
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == 27:  # Q veya ESC
            print("\n✓ Çıkış yapılıyor...")
            break
        elif key == ord(' '):  # SPACE
            stabilization_enabled = not stabilization_enabled
            status = "AÇIK" if stabilization_enabled else "KAPALI"
            print(f"\n→ Stabilizasyon: {status}")
        elif key == ord('r'):  # R
            stabilizer.reset()
            print("\n→ Stabilizatör sıfırlandı")
        elif key == ord('+') or key == ord('='):
            stabilizer.smoothing_factor = min(1.0, stabilizer.smoothing_factor + 0.05)
            print(f"\n→ Yumuşatma faktörü: {stabilizer.smoothing_factor:.2f}")
        elif key == ord('-') or key == ord('_'):
            stabilizer.smoothing_factor = max(0.0, stabilizer.smoothing_factor - 0.05)
            print(f"\n→ Yumuşatma faktörü: {stabilizer.smoothing_factor:.2f}")
    
    # Temizlik
    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Program sonlandırıldı.")
    print("\nİstatistikler:")
    print(f"  Ortalama FPS: {np.mean(fps_list):.1f}")
    if stabilizer.motion_history:
        print(f"  Ortalama Hareket: {np.mean(stabilizer.motion_history):.2f} px")


if __name__ == "__main__":
    main()