import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

# ========== KALMAN FİLTRESİ SINIFI ==========
class KalmanFilter:
    def __init__(self, dt, process_noise, measurement_noise):
        """
        Kalman Filtresi için başlangıç parametreleri
        dt: Zaman adımı
        process_noise: Süreç gürültüsü (Q)
        measurement_noise: Ölçüm gürültüsü (R)
        """
        self.dt = dt
        
        # Durum vektörü: [x, y, vx, vy]
        self.x = np.zeros((4, 1))
        
        # Durum geçiş matrisi (kinematik model)
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Ölçüm matrisi (sadece pozisyon ölçüyoruz)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Kovaryans matrisi
        self.P = np.eye(4) * 1000
        
        # Süreç gürültüsü kovaryansı
        self.Q = np.eye(4) * process_noise
        
        # Ölçüm gürültüsü kovaryansı
        self.R = np.eye(2) * measurement_noise
        
    def predict(self, ax=0, ay=-9.8):
        """Tahmin adımı (yerçekimi ile)"""
        # Kontrol girişi (yerçekimi)
        B = np.array([
            [0.5 * self.dt**2, 0],
            [0, 0.5 * self.dt**2],
            [self.dt, 0],
            [0, self.dt]
        ])
        u = np.array([[ax], [ay]])
        
        # Durum tahmini
        self.x = self.F @ self.x + B @ u
        
        # Kovaryans tahmini
        self.P = self.F @ self.P @ self.F.T + self.Q
        
    def update(self, measurement):
        """Güncelleme adımı (ölçüm ile düzeltme)"""
        # Kalman kazancı
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Durum güncelleme
        y = measurement - self.H @ self.x  # İnovasyon
        self.x = self.x + K @ y
        
        # Kovaryans güncelleme
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
    def get_state(self):
        """Mevcut durumu döndür"""
        return self.x.flatten()

# ========== SİMÜLASYON PARAMETRELERİ ==========
g = 9.8
v0 = 50
angle = 45
dt = 0.05
e = 0.7

# Gürültü parametreleri
measurement_noise = 2.0  # Ölçüm gürültüsü (metre)
process_noise = 0.1      # Süreç gürültüsü

# Başlangıç değerleri
def initialize_motion(v0, angle):
    angle_rad = np.radians(angle)
    vx = v0 * np.cos(angle_rad)
    vy = v0 * np.sin(angle_rad)
    return vx, vy, 0, 0, 0

vx, vy, x, y, t = initialize_motion(v0, angle)
x_true, y_true = [x], [y]
x_measured, y_measured = [x], [y]
x_kalman, y_kalman = [x], [y]
errors = []
is_running = False

# Kalman filtresi başlat
kf = KalmanFilter(dt, process_noise, measurement_noise)
kf.x = np.array([[x], [y], [vx], [vy]])

# ========== GRAFİK OLUŞTURMA ==========
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 2, left=0.08, right=0.95, top=0.92, bottom=0.35, 
                      hspace=0.3, wspace=0.25)

# Ana yörünge grafiği
ax_main = fig.add_subplot(gs[0:2, :])
ax_main.set_xlim(0, 300)
ax_main.set_ylim(0, 150)
ax_main.set_xlabel('Mesafe (m)', fontsize=12, fontweight='bold')
ax_main.set_ylabel('Yükseklik (m)', fontsize=12, fontweight='bold')
ax_main.set_title('Kalman Filtreli Top Yörüngesi Simülasyonu', fontsize=14, fontweight='bold')
ax_main.grid(True, alpha=0.3)
ax_main.axhline(y=0, color='green', linewidth=2.5, alpha=0.7)

# Çizimler
line_true, = ax_main.plot([], [], 'b-', linewidth=2, label='Gerçek Yörünge', alpha=0.8)
line_measured, = ax_main.plot([], [], 'r.', markersize=4, label='Gürültülü Ölçümler', alpha=0.5)
line_kalman, = ax_main.plot([], [], 'g-', linewidth=2.5, label='Kalman Tahmini', alpha=0.9)
ball_true, = ax_main.plot([], [], 'bo', markersize=12, label='Gerçek Top')
ball_kalman, = ax_main.plot([], [], 'go', markersize=14, label='Tahmin Edilen Top', alpha=0.7)

text_info = ax_main.text(0.02, 0.97, '', transform=ax_main.transAxes, 
                         verticalalignment='top', fontsize=9,
                         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
ax_main.legend(loc='upper right', fontsize=9)

# RMSE grafiği
ax_rmse = fig.add_subplot(gs[2, 0])
ax_rmse.set_xlabel('Zaman (s)', fontsize=10)
ax_rmse.set_ylabel('RMSE (m)', fontsize=10)
ax_rmse.set_title('Hata Analizi (RMSE)', fontsize=11, fontweight='bold')
ax_rmse.grid(True, alpha=0.3)
line_rmse, = ax_rmse.plot([], [], 'r-', linewidth=2)

# Konum hatası grafiği
ax_error = fig.add_subplot(gs[2, 1])
ax_error.set_xlabel('Zaman (s)', fontsize=10)
ax_error.set_ylabel('Konum Hatası (m)', fontsize=10)
ax_error.set_title('Anlık Konum Hatası', fontsize=11, fontweight='bold')
ax_error.grid(True, alpha=0.3)
line_error_x, = ax_error.plot([], [], 'b-', linewidth=2, label='X Hatası', alpha=0.7)
line_error_y, = ax_error.plot([], [], 'r-', linewidth=2, label='Y Hatası', alpha=0.7)
ax_error.legend(fontsize=8)

# ========== KONTROLLER ==========
plt.subplots_adjust(bottom=0.35)
ax_v0 = plt.axes([0.15, 0.24, 0.7, 0.02])
ax_angle = plt.axes([0.15, 0.20, 0.7, 0.02])
ax_gravity = plt.axes([0.15, 0.16, 0.7, 0.02])
ax_meas_noise = plt.axes([0.15, 0.12, 0.7, 0.02])
ax_proc_noise = plt.axes([0.15, 0.08, 0.7, 0.02])

slider_v0 = Slider(ax_v0, 'Hız (m/s)', 10, 100, valinit=v0, valstep=1)
slider_angle = Slider(ax_angle, 'Açı (°)', 0, 90, valinit=angle, valstep=1)
slider_gravity = Slider(ax_gravity, 'Yerçekimi (m/s²)', 1, 20, valinit=g, valstep=0.1)
slider_meas_noise = Slider(ax_meas_noise, 'Ölçüm Gürültüsü', 0.1, 10, valinit=measurement_noise, valstep=0.1)
slider_proc_noise = Slider(ax_proc_noise, 'Süreç Gürültüsü', 0.01, 1, valinit=process_noise, valstep=0.01)

ax_start = plt.axes([0.25, 0.02, 0.15, 0.04])
ax_reset = plt.axes([0.6, 0.02, 0.15, 0.04])
btn_start = Button(ax_start, 'Başlat/Duraklat', color='lightgreen')
btn_reset = Button(ax_reset, 'Sıfırla', color='lightcoral')

def update_params(val):
    global v0, angle, g, measurement_noise, process_noise, is_running
    if not is_running:
        v0 = slider_v0.val
        angle = slider_angle.val
        g = slider_gravity.val
        measurement_noise = slider_meas_noise.val
        process_noise = slider_proc_noise.val
        reset_simulation()

slider_v0.on_changed(update_params)
slider_angle.on_changed(update_params)
slider_gravity.on_changed(update_params)
slider_meas_noise.on_changed(update_params)
slider_proc_noise.on_changed(update_params)

def reset_simulation():
    global x, y, vx, vy, t, x_true, y_true, x_measured, y_measured, x_kalman, y_kalman, errors, kf
    vx, vy, x, y, t = initialize_motion(v0, angle)
    x_true, y_true = [x], [y]
    x_measured, y_measured = [x], [y]
    x_kalman, y_kalman = [x], [y]
    errors = []
    
    # Kalman filtresini yeniden başlat
    kf = KalmanFilter(dt, process_noise, measurement_noise)
    kf.x = np.array([[x], [y], [vx], [vy]])
    
    # Grafikleri temizle
    line_true.set_data([], [])
    line_measured.set_data([], [])
    line_kalman.set_data([], [])
    ball_true.set_data([], [])
    ball_kalman.set_data([], [])
    line_rmse.set_data([], [])
    line_error_x.set_data([], [])
    line_error_y.set_data([], [])
    text_info.set_text('')

def toggle_animation(event):
    global is_running
    is_running = not is_running
    if is_running:
        ani.event_source.start()
    else:
        ani.event_source.stop()

def reset_button(event):
    global is_running
    is_running = False
    ani.event_source.stop()
    reset_simulation()
    fig.canvas.draw_idle()

btn_start.on_clicked(toggle_animation)
btn_reset.on_clicked(reset_button)

def animate(frame):
    global x, y, vx, vy, t, x_true, y_true, x_measured, y_measured, x_kalman, y_kalman, errors
    
    if not is_running:
        return line_true, line_measured, line_kalman, ball_true, ball_kalman, text_info
    
    # Gerçek fizik (ground truth)
    vy -= g * dt
    x += vx * dt
    y += vy * dt
    t += dt
    
    # Yere çarpma
    if y < 0:
        y = 0
        vy = -vy * e
        if abs(vy) < 0.5:
            vy = 0
    
    # Gerçek veriyi kaydet
    x_true.append(x)
    y_true.append(y)
    
    # Gürültülü ölçüm oluştur (sensör simulasyonu)
    noise_x = np.random.normal(0, measurement_noise)
    noise_y = np.random.normal(0, measurement_noise)
    x_meas = x + noise_x
    y_meas = max(0, y + noise_y)  # Yerin altına inmesin
    
    x_measured.append(x_meas)
    y_measured.append(y_meas)
    
    # Kalman filtresi tahmini
    kf.predict(ax=0, ay=-g)
    measurement = np.array([[x_meas], [y_meas]])
    kf.update(measurement)
    
    state = kf.get_state()
    x_kal, y_kal = state[0], state[1]
    x_kalman.append(x_kal)
    y_kalman.append(max(0, y_kal))
    
    # Hata hesaplama
    error = np.sqrt((x - x_kal)**2 + (y - y_kal)**2)
    errors.append(error)
    
    # Grafik sınırlarını güncelle
    if x > ax_main.get_xlim()[1] - 20:
        ax_main.set_xlim(0, x + 50)
    
    # Ana grafik güncelleme
    line_true.set_data(x_true, y_true)
    line_measured.set_data(x_measured, y_measured)
    line_kalman.set_data(x_kalman, y_kalman)
    ball_true.set_data([x], [y])
    ball_kalman.set_data([x_kal], [max(0, y_kal)])
    
    # RMSE hesaplama
    if len(errors) > 0:
        times = np.arange(len(errors)) * dt
        rmse = np.sqrt(np.mean(np.array(errors)**2))
        
        # RMSE grafiği
        cumulative_rmse = [np.sqrt(np.mean(np.array(errors[:i+1])**2)) for i in range(len(errors))]
        line_rmse.set_data(times, cumulative_rmse)
        ax_rmse.set_xlim(0, max(times[-1], 1))
        ax_rmse.set_ylim(0, max(cumulative_rmse) * 1.2 if max(cumulative_rmse) > 0 else 1)
        
        # Konum hatası grafiği
        error_x = np.array(x_true) - np.array(x_kalman)
        error_y = np.array(y_true) - np.array(y_kalman)
        line_error_x.set_data(times, error_x)
        line_error_y.set_data(times, error_y)
        ax_error.set_xlim(0, max(times[-1], 1))
        max_err = max(abs(error_x).max(), abs(error_y).max()) if len(error_x) > 0 else 1
        ax_error.set_ylim(-max_err * 1.2, max_err * 1.2)
        
        # Bilgi metni
        info_text = f'━━━ Zaman: {t:.2f} s ━━━\n\n'
        info_text += f'📍 GERÇEK POZİSYON:\n   ({x:.2f}, {y:.2f}) m\n\n'
        info_text += f'📡 ÖLÇÜLEN POZİSYON:\n   ({x_meas:.2f}, {y_meas:.2f}) m\n\n'
        info_text += f'🎯 KALMAN TAHMİNİ:\n   ({x_kal:.2f}, {y_kal:.2f}) m\n\n'
        info_text += f'📊 RMSE: {rmse:.3f} m\n'
        info_text += f'❌ Anlık Hata: {error:.3f} m'
        text_info.set_text(info_text)
    
    return line_true, line_measured, line_kalman, ball_true, ball_kalman, text_info

# Animasyon
ani = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)
ani.event_source.stop()

plt.show()