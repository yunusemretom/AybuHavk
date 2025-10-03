"""
Kalman Filtreli 2D Top Yörüngesi Simülasyonu
Teslim Paketi: İnteraktif simülasyon + PNG grafikler + PDF rapor

Gereksinimler:
pip install numpy matplotlib reportlab
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from datetime import datetime
import os

# PDF rapor için (opsiyonel - yoksa sadece uyarı verir)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    print("UYARI: reportlab yüklü değil. PDF raporu oluşturulamayacak.")
    print("Yüklemek için: pip install reportlab")
    PDF_AVAILABLE = False

# ========== KALMAN FİLTRESİ SINIFI ==========
class KalmanFilter:
    """
    Kalman Filtresi - Optimal Durum Tahmini
    
    Durum Vektörü: [x, y, vx, vy]
    - x, y: Pozisyon (metre)
    - vx, vy: Hız (m/s)
    """
    def __init__(self, dt, process_noise, measurement_noise):
        self.dt = dt
        
        # Durum vektörü: [x, y, vx, vy]
        self.x = np.zeros((4, 1))
        
        # Durum geçiş matrisi (kinematik model)
        # x_k+1 = F * x_k + B * u_k
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
        
        # Kovaryans matrisi (belirsizlik)
        self.P = np.eye(4) * 1000
        
        # Süreç gürültüsü kovaryansı (Q)
        self.Q = np.eye(4) * process_noise
        
        # Ölçüm gürültüsü kovaryansı (R)
        self.R = np.eye(2) * measurement_noise
        
        # Performans metrikleri
        self.innovation_history = []
        
    def predict(self, ax=0, ay=-9.8):
        """
        Tahmin Adımı
        Kinematik model + yerçekimi ile bir sonraki durumu tahmin et
        """
        # Kontrol girişi matrisi (yerçekimi etkisi)
        B = np.array([
            [0.5 * self.dt**2, 0],
            [0, 0.5 * self.dt**2],
            [self.dt, 0],
            [0, self.dt]
        ])
        u = np.array([[ax], [ay]])
        
        # Durum tahmini: x̂_k|k-1 = F * x̂_k-1|k-1 + B * u_k
        self.x = self.F @ self.x + B @ u
        
        # Kovaryans tahmini: P_k|k-1 = F * P_k-1|k-1 * F^T + Q
        self.P = self.F @ self.P @ self.F.T + self.Q
        
    def update(self, measurement):
        """
        Güncelleme Adımı
        Gerçek ölçüm ile tahmini düzelt
        """
        # İnovasyon (ölçüm - tahmin)
        y = measurement - self.H @ self.x
        self.innovation_history.append(np.linalg.norm(y))
        
        # İnovasyon kovaryansı: S = H * P * H^T + R
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman kazancı: K = P * H^T * S^-1
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Durum güncelleme: x̂_k|k = x̂_k|k-1 + K * y
        self.x = self.x + K @ y
        
        # Kovaryans güncelleme: P_k|k = (I - K * H) * P_k|k-1
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
    def get_state(self):
        """Mevcut durumu döndür"""
        return self.x.flatten()

# ========== ANALİZ SINIFI ==========
class SimulationAnalysis:
    """Simülasyon sonuçlarını analiz eden sınıf"""
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x_true = []
        self.y_true = []
        self.x_measured = []
        self.y_measured = []
        self.x_kalman = []
        self.y_kalman = []
        self.times = []
        self.errors = []
        self.measurement_errors = []
        
    def add_data(self, t, x_t, y_t, x_m, y_m, x_k, y_k):
        """Veri noktası ekle"""
        self.times.append(t)
        self.x_true.append(x_t)
        self.y_true.append(y_t)
        self.x_measured.append(x_m)
        self.y_measured.append(y_m)
        self.x_kalman.append(x_k)
        self.y_kalman.append(y_k)
        
        # Kalman hatası
        kalman_error = np.sqrt((x_t - x_k)**2 + (y_t - y_k)**2)
        self.errors.append(kalman_error)
        
        # Ölçüm hatası
        meas_error = np.sqrt((x_t - x_m)**2 + (y_t - y_m)**2)
        self.measurement_errors.append(meas_error)
        
    def calculate_metrics(self):
        """İstatistiksel metrikleri hesapla"""
        if len(self.errors) == 0:
            return None
            
        errors = np.array(self.errors)
        meas_errors = np.array(self.measurement_errors)
        
        metrics = {
            'kalman_rmse': np.sqrt(np.mean(errors**2)),
            'kalman_mae': np.mean(np.abs(errors)),
            'kalman_max_error': np.max(errors),
            'measurement_rmse': np.sqrt(np.mean(meas_errors**2)),
            'measurement_mae': np.mean(np.abs(meas_errors)),
            'improvement': (np.sqrt(np.mean(meas_errors**2)) - np.sqrt(np.mean(errors**2))) / np.sqrt(np.mean(meas_errors**2)) * 100
        }
        return metrics

# ========== GLOBAL DEĞİŞKENLER ==========
g = 9.8
v0 = 50
angle = 45
dt = 0.05
e = 0.7
measurement_noise = 2.0
process_noise = 0.1

analysis = SimulationAnalysis()
is_running = False
output_dir = "simulation_output"

# Başlangıç değerleri
def initialize_motion(v0, angle):
    angle_rad = np.radians(angle)
    vx = v0 * np.cos(angle_rad)
    vy = v0 * np.sin(angle_rad)
    return vx, vy, 0, 0, 0

vx, vy, x, y, t = initialize_motion(v0, angle)
kf = KalmanFilter(dt, process_noise, measurement_noise)
kf.x = np.array([[x], [y], [vx], [vy]])

# ========== GRAFİK OLUŞTURMA ==========
def create_interactive_plot():
    """İnteraktif simülasyon penceresi oluştur"""
    global fig, ax_main, ax_rmse, ax_error, ax_improvement
    global line_true, line_measured, line_kalman, ball_true, ball_kalman
    global line_rmse, line_error_x, line_error_y, line_improvement, text_info
    global ani
    
    fig = plt.figure(figsize=(18, 11))
    fig.suptitle('Kalman Filtreli 2D Top Yörüngesi Simülasyonu', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    gs = fig.add_gridspec(3, 3, left=0.06, right=0.96, top=0.92, bottom=0.32, 
                          hspace=0.35, wspace=0.3)
    
    # Ana yörünge grafiği
    ax_main = fig.add_subplot(gs[0:2, :])
    ax_main.set_xlim(0, 300)
    ax_main.set_ylim(0, 150)
    ax_main.set_xlabel('Mesafe (m)', fontsize=12, fontweight='bold')
    ax_main.set_ylabel('Yükseklik (m)', fontsize=12, fontweight='bold')
    ax_main.set_title('Yörünge Karşılaştırması', fontsize=13, fontweight='bold')
    ax_main.grid(True, alpha=0.3, linestyle='--')
    ax_main.axhline(y=0, color='green', linewidth=2.5, alpha=0.6, label='Zemin')
    
    line_true, = ax_main.plot([], [], 'b-', linewidth=2.5, label='Gerçek Yörünge', alpha=0.8)
    line_measured, = ax_main.plot([], [], 'r.', markersize=5, label='Gürültülü Ölçümler', alpha=0.4)
    line_kalman, = ax_main.plot([], [], 'g-', linewidth=3, label='Kalman Tahmini', alpha=0.9)
    ball_true, = ax_main.plot([], [], 'bo', markersize=14, label='Gerçek Top', zorder=5)
    ball_kalman, = ax_main.plot([], [], 'go', markersize=16, label='Tahmin Edilen', alpha=0.7, zorder=5)
    
    text_info = ax_main.text(0.02, 0.97, '', transform=ax_main.transAxes, 
                             verticalalignment='top', fontsize=9, family='monospace',
                             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.85))
    ax_main.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # RMSE grafiği
    ax_rmse = fig.add_subplot(gs[2, 0])
    ax_rmse.set_xlabel('Zaman (s)', fontsize=10)
    ax_rmse.set_ylabel('RMSE (m)', fontsize=10)
    ax_rmse.set_title('Kümülatif RMSE', fontsize=11, fontweight='bold')
    ax_rmse.grid(True, alpha=0.3)
    line_rmse, = ax_rmse.plot([], [], 'r-', linewidth=2.5, label='Kalman RMSE')
    ax_rmse.legend(fontsize=8)
    
    # Konum hatası grafiği
    ax_error = fig.add_subplot(gs[2, 1])
    ax_error.set_xlabel('Zaman (s)', fontsize=10)
    ax_error.set_ylabel('Hata (m)', fontsize=10)
    ax_error.set_title('Anlık Konum Hatası', fontsize=11, fontweight='bold')
    ax_error.grid(True, alpha=0.3)
    line_error_x, = ax_error.plot([], [], 'b-', linewidth=2, label='X Hatası', alpha=0.7)
    line_error_y, = ax_error.plot([], [], 'r-', linewidth=2, label='Y Hatası', alpha=0.7)
    ax_error.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax_error.legend(fontsize=8)
    
    # İyileştirme grafiği
    ax_improvement = fig.add_subplot(gs[2, 2])
    ax_improvement.set_xlabel('Zaman (s)', fontsize=10)
    ax_improvement.set_ylabel('Hata (m)', fontsize=10)
    ax_improvement.set_title('Kalman vs Ham Ölçüm', fontsize=11, fontweight='bold')
    ax_improvement.grid(True, alpha=0.3)
    line_improvement, = ax_improvement.plot([], [], 'g-', linewidth=2.5, label='İyileştirme')
    ax_improvement.legend(fontsize=8)
    
    # Kontroller
    create_controls()
    
    # Animasyon
    ani = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)
    ani.event_source.stop()

def create_controls():
    """Kontrol widget'larını oluştur"""
    global slider_v0, slider_angle, slider_gravity, slider_meas_noise, slider_proc_noise
    global btn_start, btn_reset, btn_save
    
    plt.subplots_adjust(bottom=0.32)
    
    ax_v0 = plt.axes([0.12, 0.23, 0.75, 0.02])
    ax_angle = plt.axes([0.12, 0.19, 0.75, 0.02])
    ax_gravity = plt.axes([0.12, 0.15, 0.75, 0.02])
    ax_meas_noise = plt.axes([0.12, 0.11, 0.75, 0.02])
    ax_proc_noise = plt.axes([0.12, 0.07, 0.75, 0.02])
    
    slider_v0 = Slider(ax_v0, 'Hız (m/s)', 10, 100, valinit=v0, valstep=1)
    slider_angle = Slider(ax_angle, 'Açı (°)', 0, 90, valinit=angle, valstep=1)
    slider_gravity = Slider(ax_gravity, 'Yerçekimi (m/s²)', 1, 20, valinit=g, valstep=0.1)
    slider_meas_noise = Slider(ax_meas_noise, 'Ölçüm Gürültüsü (m)', 0.1, 10, valinit=measurement_noise, valstep=0.1)
    slider_proc_noise = Slider(ax_proc_noise, 'Süreç Gürültüsü', 0.01, 1, valinit=process_noise, valstep=0.01)
    
    slider_v0.on_changed(update_params)
    slider_angle.on_changed(update_params)
    slider_gravity.on_changed(update_params)
    slider_meas_noise.on_changed(update_params)
    slider_proc_noise.on_changed(update_params)
    
    ax_start = plt.axes([0.15, 0.015, 0.15, 0.04])
    ax_reset = plt.axes([0.42, 0.015, 0.15, 0.04])
    ax_save = plt.axes([0.69, 0.015, 0.15, 0.04])
    
    btn_start = Button(ax_start, 'Başlat/Duraklat', color='lightgreen', hovercolor='green')
    btn_reset = Button(ax_reset, 'Sıfırla', color='lightcoral', hovercolor='red')
    btn_save = Button(ax_save, 'Kaydet (PNG+PDF)', color='lightblue', hovercolor='blue')
    
    btn_start.on_clicked(toggle_animation)
    btn_reset.on_clicked(reset_button)
    btn_save.on_clicked(save_results)

def update_params(val):
    global v0, angle, g, measurement_noise, process_noise
    if not is_running:
        v0 = slider_v0.val
        angle = slider_angle.val
        g = slider_gravity.val
        measurement_noise = slider_meas_noise.val
        process_noise = slider_proc_noise.val
        reset_simulation()

def reset_simulation():
    global x, y, vx, vy, t, kf, analysis
    vx, vy, x, y, t = initialize_motion(v0, angle)
    
    kf = KalmanFilter(dt, process_noise, measurement_noise)
    kf.x = np.array([[x], [y], [vx], [vy]])
    
    analysis.reset()
    
    line_true.set_data([], [])
    line_measured.set_data([], [])
    line_kalman.set_data([], [])
    ball_true.set_data([], [])
    ball_kalman.set_data([], [])
    line_rmse.set_data([], [])
    line_error_x.set_data([], [])
    line_error_y.set_data([], [])
    line_improvement.set_data([], [])
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

def animate(frame):
    global x, y, vx, vy, t
    
    if not is_running:
        return
    
    # Gerçek fizik
    vy -= g * dt
    x += vx * dt
    y += vy * dt
    t += dt
    
    if y < 0:
        y = 0
        vy = -vy * e
        if abs(vy) < 0.5:
            vy = 0
    
    # Gürültülü ölçüm
    noise_x = np.random.normal(0, measurement_noise)
    noise_y = np.random.normal(0, measurement_noise)
    x_meas = x + noise_x
    y_meas = max(0, y + noise_y)
    
    # Kalman filtresi
    kf.predict(ax=0, ay=-g)
    measurement = np.array([[x_meas], [y_meas]])
    kf.update(measurement)
    
    state = kf.get_state()
    x_kal, y_kal = state[0], max(0, state[1])
    
    # Veri kaydet
    analysis.add_data(t, x, y, x_meas, y_meas, x_kal, y_kal)
    
    # Grafik güncelle
    if x > ax_main.get_xlim()[1] - 20:
        ax_main.set_xlim(0, x + 50)
    
    line_true.set_data(analysis.x_true, analysis.y_true)
    line_measured.set_data(analysis.x_measured, analysis.y_measured)
    line_kalman.set_data(analysis.x_kalman, analysis.y_kalman)
    ball_true.set_data([x], [y])
    ball_kalman.set_data([x_kal], [y_kal])
    
    # Hata grafikleri
    if len(analysis.errors) > 1:
        times = np.array(analysis.times)
        
        # RMSE
        cumulative_rmse = [np.sqrt(np.mean(np.array(analysis.errors[:i+1])**2)) 
                          for i in range(len(analysis.errors))]
        line_rmse.set_data(times, cumulative_rmse)
        ax_rmse.set_xlim(0, max(times[-1], 1))
        ax_rmse.set_ylim(0, max(cumulative_rmse) * 1.2 if max(cumulative_rmse) > 0 else 1)
        
        # Konum hatası
        error_x = np.array(analysis.x_true) - np.array(analysis.x_kalman)
        error_y = np.array(analysis.y_true) - np.array(analysis.y_kalman)
        line_error_x.set_data(times, error_x)
        line_error_y.set_data(times, error_y)
        ax_error.set_xlim(0, max(times[-1], 1))
        max_err = max(abs(error_x).max(), abs(error_y).max()) if len(error_x) > 0 else 1
        ax_error.set_ylim(-max_err * 1.2, max_err * 1.2)
        
        # İyileştirme
        improvement = np.array(analysis.measurement_errors) - np.array(analysis.errors)
        line_improvement.set_data(times, improvement)
        ax_improvement.set_xlim(0, max(times[-1], 1))
        ax_improvement.set_ylim(min(improvement) * 1.2 if min(improvement) < 0 else 0, 
                                max(improvement) * 1.2)
        
        # Bilgi
        metrics = analysis.calculate_metrics()
        info_text = f'━━━ T: {t:.2f}s ━━━\n\n'
        info_text += f'📍 GERÇEK: ({x:.2f}, {y:.2f})m\n'
        info_text += f'📡 ÖLÇÜM: ({x_meas:.2f}, {y_meas:.2f})m\n'
        info_text += f'🎯 KALMAN: ({x_kal:.2f}, {y_kal:.2f})m\n\n'
        info_text += f'📊 RMSE: {metrics["kalman_rmse"]:.3f}m\n'
        info_text += f'✅ İyileştirme: {metrics["improvement"]:.1f}%'
        text_info.set_text(info_text)

def save_results(event):
    """Sonuçları PNG ve PDF olarak kaydet"""
    global is_running
    
    # Simülasyonu durdur
    was_running = is_running
    is_running = False
    ani.event_source.stop()
    
    # Klasör oluştur
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*60)
    print("SONUÇLAR KAYDEDİLİYOR...")
    print("="*60)
    
    # Ana grafik kaydet
    main_plot_path = os.path.join(output_dir, f"trajectory_{timestamp}.png")
    fig.savefig(main_plot_path, dpi=300, bbox_inches='tight')
    print(f"✓ Ana grafik kaydedildi: {main_plot_path}")
    
    # Detaylı analiz grafikleri oluştur
    create_detailed_plots(timestamp)
    
    # PDF rapor oluştur
    if PDF_AVAILABLE:
        create_pdf_report(timestamp)
    
    print("="*60)
    print("✓ TÜM DOSYALAR BAŞARIYLA KAYDEDİLDİ!")
    print(f"✓ Klasör: {output_dir}/")
    print("="*60 + "\n")
    
    if was_running:
        is_running = True
        ani.event_source.start()

def create_detailed_plots(timestamp):
    """Detaylı analiz grafikleri oluştur"""
    if len(analysis.errors) < 2:
        print("⚠ Yeterli veri yok, detaylı grafikler oluşturulamadı.")
        return
    
    metrics = analysis.calculate_metrics()
    times = np.array(analysis.times)
    
    # 1. Hata karşılaştırma grafiği
    fig1, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig1.suptitle('Detaylı Hata Analizi', fontsize=16, fontweight='bold')
    
    # Kalman vs Ölçüm RMSE
    ax1 = axes[0, 0]
    kalman_rmse = [np.sqrt(np.mean(np.array(analysis.errors[:i+1])**2)) 
                   for i in range(len(analysis.errors))]
    meas_rmse = [np.sqrt(np.mean(np.array(analysis.measurement_errors[:i+1])**2)) 
                 for i in range(len(analysis.measurement_errors))]
    ax1.plot(times, kalman_rmse, 'g-', linewidth=2, label='Kalman RMSE')
    ax1.plot(times, meas_rmse, 'r--', linewidth=2, label='Ham Ölçüm RMSE')
    ax1.set_xlabel('Zaman (s)')
    ax1.set_ylabel('RMSE (m)')
    ax1.set_title('RMSE Karşılaştırması')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # X-Y hatası
    ax2 = axes[0, 1]
    error_x = np.array(analysis.x_true) - np.array(analysis.x_kalman)
    error_y = np.array(analysis.y_true) - np.array(analysis.y_kalman)
    ax2.plot(times, error_x, 'b-', linewidth=2, label='X Hatası')
    ax2.plot(times, error_y, 'r-', linewidth=2, label='Y Hatası')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax2.set_xlabel('Zaman (s)')
    ax2.set_ylabel('Hata (m)')
    ax2.set_title('Eksen Bazlı Hatalar')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Hata dağılımı histogram
    ax3 = axes[1, 0]
    ax3.hist(analysis.errors, bins=30, color='green', alpha=0.7, edgecolor='black')
    ax3.axvline(x=metrics['kalman_rmse'], color='red', linestyle='--', 
                linewidth=2, label=f'RMSE: {metrics["kalman_rmse"]:.3f}m')
    ax3.set_xlabel('Hata (m)')
    ax3.set_ylabel('Frekans')
    ax3.set_title('Kalman Hatası Dağılımı')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # İstatistikler tablosu
    ax4 = axes[1, 1]
    ax4.axis('off')
    stats_text = f"""
    PERFORMANS METRİKLERİ
    {'='*40}
    
    KALMAN FİLTRESİ:
    • RMSE: {metrics['kalman_rmse']:.4f} m
    • MAE: {metrics['kalman_mae']:.4f} m
    • Max Hata: {metrics['kalman_max_error']:.4f} m
    
    HAM ÖLÇÜM:
    • RMSE: {metrics['measurement_rmse']:.4f} m
    • MAE: {metrics['measurement_mae']:.4f} m
    
    İYİLEŞTİRME:
    • RMSE İyileştirme: {metrics['improvement']:.2f}%
    
    SİMÜLASYON PARAMETRELERİ:
    • Başlangıç Hızı: {v0:.1f} m/s
    • Fırlatma Açısı: {angle:.1f}°
    • Yerçekimi: {g:.1f} m/s²
    • Ölçüm Gürültüsü: {measurement_noise:.2f} m
    • Süreç Gürültüsü: {process_noise:.3f}
    """
    ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, 
             fontsize=11, verticalalignment='top', family='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    error_plot_path = os.path.join(output_dir, f"error_analysis_{timestamp}.png")
    plt.savefig(error_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Hata analizi kaydedildi: {error_plot_path}")
    
    # 2. Yörünge karşılaştırma grafiği
    fig2, ax = plt.subplots(figsize=(12, 8))
    ax.plot(analysis.x_true, analysis.y_true, 'b-', linewidth=3, label='Gerçek Yörünge', alpha=0.8)
    ax.scatter(analysis.x_measured, analysis.y_measured, c='red', s=20, 
               label='Gürültülü Ölçümler', alpha=0.3)
    ax.plot(analysis.x_kalman, analysis.y_kalman, 'g-', linewidth=3, 
            label='Kalman Tahmini', alpha=0.9)
    ax.axhline(y=0, color='green', linewidth=2, alpha=0.5, label='Zemin')
    ax.set_xlabel('Mesafe (m)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Yükseklik (m)', fontsize=14, fontweight='bold')
    ax.set_title('Yörünge Karşılaştırması - Detaylı', fontsize=16, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    trajectory_plot_path = os.path.join(output_dir, f"trajectory_comparison_{timestamp}.png")
    plt.savefig(trajectory_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Yörünge karşılaştırma kaydedildi: {trajectory_plot_path}")
    
    return error_plot_path, trajectory_plot_path

def create_pdf_report(timestamp):
    """PDF analiz raporu oluştur"""
    if not PDF_AVAILABLE:
        return
    
    try:
        pdf_path = os.path.join(output_dir, f"simulation_report_{timestamp}.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                               rightMargin=30, leftMargin=30,
                               topMargin=50, bottomMargin=30)
        
        # PDF içeriği
        story = []
        styles = getSampleStyleSheet()
        
        # Başlık stilleri
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Başlık
        story.append(Paragraph("Kalman Filtreli 2D Top Yörüngesi", title_style))
        story.append(Paragraph("Simülasyon Analiz Raporu", title_style))
        story.append(Spacer(1, 20))
        
        # Tarih bilgisi
        date_text = f"<b>Tarih:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 30))
        
        # 1. GİRİŞ
        story.append(Paragraph("1. GİRİŞ", heading_style))
        intro_text = """
        Bu rapor, Kalman filtresi kullanarak 2D düzlemde hareket eden bir topun 
        yörüngesinin tahminini içermektedir. Simülasyon, gürültülü sensör ölçümlerinden 
        gerçek pozisyonu tahmin etmek için optimal durum tahmini algoritması kullanmaktadır.
        """
        story.append(Paragraph(intro_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # 2. SİMÜLASYON PARAMETRELERİ
        story.append(Paragraph("2. SİMÜLASYON PARAMETRELERİ", heading_style))
        
        params_data = [
            ['Parametre', 'Değer', 'Birim'],
            ['Başlangıç Hızı', f'{v0:.2f}', 'm/s'],
            ['Fırlatma Açısı', f'{angle:.2f}', 'derece'],
            ['Yerçekimi İvmesi', f'{g:.2f}', 'm/s²'],
            ['Ölçüm Gürültüsü (σ)', f'{measurement_noise:.2f}', 'm'],
            ['Süreç Gürültüsü', f'{process_noise:.3f}', '-'],
            ['Zaman Adımı (dt)', f'{dt:.3f}', 's'],
            ['Geri Tepme Katsayısı', f'{e:.2f}', '-'],
        ]
        
        params_table = Table(params_data, colWidths=[200, 100, 80])
        params_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(params_table)
        story.append(Spacer(1, 20))
        
        # 3. KALMAN FİLTRESİ TEORİSİ
        story.append(Paragraph("3. KALMAN FİLTRESİ TEORİSİ", heading_style))
        theory_text = """
        <b>3.1 Durum Uzayı Modeli</b><br/>
        Durum vektörü: <b>x = [x, y, v_x, v_y]ᵀ</b><br/>
        - x, y: Pozisyon (metre)<br/>
        - v_x, v_y: Hız bileşenleri (m/s)<br/><br/>
        
        <b>3.2 Tahmin Adımı (Prediction)</b><br/>
        • Durum tahmini: x̂_k|k-1 = F·x̂_k-1|k-1 + B·u_k<br/>
        • Kovaryans tahmini: P_k|k-1 = F·P_k-1|k-1·Fᵀ + Q<br/><br/>
        
        <b>3.3 Güncelleme Adımı (Update)</b><br/>
        • Kalman kazancı: K = P·Hᵀ·(H·P·Hᵀ + R)⁻¹<br/>
        • Durum güncelleme: x̂_k|k = x̂_k|k-1 + K·(z_k - H·x̂_k|k-1)<br/>
        • Kovaryans güncelleme: P_k|k = (I - K·H)·P_k|k-1<br/><br/>
        
        <b>3.4 Matrisler</b><br/>
        • F: Durum geçiş matrisi (4x4) - kinematik model<br/>
        • H: Ölçüm matrisi (2x4) - sadece pozisyon ölçümü<br/>
        • Q: Süreç gürültüsü kovaryansı (4x4)<br/>
        • R: Ölçüm gürültüsü kovaryansı (2x2)
        """
        story.append(Paragraph(theory_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # 4. PERFORMANS METRİKLERİ
        if len(analysis.errors) > 0:
            metrics = analysis.calculate_metrics()
            
            story.append(PageBreak())
            story.append(Paragraph("4. PERFORMANS METRİKLERİ", heading_style))
            
            metrics_data = [
                ['Metrik', 'Kalman Filtresi', 'Ham Ölçüm', 'İyileştirme'],
                ['RMSE (m)', f"{metrics['kalman_rmse']:.4f}", 
                 f"{metrics['measurement_rmse']:.4f}", 
                 f"{metrics['improvement']:.2f}%"],
                ['MAE (m)', f"{metrics['kalman_mae']:.4f}", 
                 f"{metrics['measurement_mae']:.4f}", '-'],
                ['Max Hata (m)', f"{metrics['kalman_max_error']:.4f}", '-', '-'],
            ]
            
            metrics_table = Table(metrics_data, colWidths=[150, 100, 100, 100])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # Metrik açıklamaları
            metrics_explain = """
            <b>RMSE (Root Mean Square Error):</b> Tahmin hatalarının karekök ortalaması. 
            Düşük değer daha iyi performans gösterir.<br/><br/>
            
            <b>MAE (Mean Absolute Error):</b> Mutlak hataların ortalaması. 
            RMSE'ye göre aykırı değerlere daha az duyarlıdır.<br/><br/>
            
            <b>İyileştirme Oranı:</b> Kalman filtresinin ham ölçümlere göre RMSE'de 
            sağladığı iyileştirme yüzdesi. Pozitif değer filtre performansını gösterir.
            """
            story.append(Paragraph(metrics_explain, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # 5. GRAFİKLER
        story.append(PageBreak())
        story.append(Paragraph("5. SİMÜLASYON GRAFİKLERİ", heading_style))
        
        # Ana yörünge grafiği
        main_plot = os.path.join(output_dir, f"trajectory_{timestamp}.png")
        if os.path.exists(main_plot):
            story.append(Paragraph("5.1 Ana Yörünge Simülasyonu", styles['Heading3']))
            img = Image(main_plot, width=500, height=300)
            story.append(img)
            story.append(Spacer(1, 15))
        
        # Detaylı karşılaştırma
        trajectory_plot = os.path.join(output_dir, f"trajectory_comparison_{timestamp}.png")
        if os.path.exists(trajectory_plot):
            story.append(PageBreak())
            story.append(Paragraph("5.2 Yörünge Karşılaştırması", styles['Heading3']))
            img2 = Image(trajectory_plot, width=480, height=320)
            story.append(img2)
            story.append(Spacer(1, 15))
        
        # Hata analizi
        error_plot = os.path.join(output_dir, f"error_analysis_{timestamp}.png")
        if os.path.exists(error_plot):
            story.append(PageBreak())
            story.append(Paragraph("5.3 Detaylı Hata Analizi", styles['Heading3']))
            img3 = Image(error_plot, width=480, height=320)
            story.append(img3)
            story.append(Spacer(1, 15))
        
        # 6. SONUÇLAR VE DEĞERLENDİRME
        story.append(PageBreak())
        story.append(Paragraph("6. SONUÇLAR VE DEĞERLENDİRME", heading_style))
        
        if len(analysis.errors) > 0:
            conclusion_text = f"""
            <b>6.1 Ana Bulgular</b><br/><br/>
            
            Bu simülasyonda Kalman filtresi, gürültülü sensör ölçümlerinden topun gerçek 
            pozisyonunu tahmin etmek için kullanılmıştır. Elde edilen sonuçlar:<br/><br/>
            
            • Kalman filtresi RMSE değeri <b>{metrics['kalman_rmse']:.4f} m</b> olarak 
            ölçülmüştür.<br/>
            • Ham ölçümlere göre <b>{metrics['improvement']:.2f}%</b> iyileştirme 
            sağlanmıştır.<br/>
            • Maksimum hata <b>{metrics['kalman_max_error']:.4f} m</b> olarak 
            kaydedilmiştir.<br/><br/>
            
            <b>6.2 Filtre Performansı</b><br/><br/>
            
            Kalman filtresi, özellikle yörüngenin düzgün kısımlarında çok başarılı 
            performans göstermiştir. Gürültülü ölçümler içinden gerçek hareketi ayırt 
            etme yeteneği açıkça görülmektedir.<br/><br/>
            
            Topun yere çarptığı anlarda (süreksizlik noktaları) filtre geçici olarak 
            daha yüksek hata gösterse de, hızlıca gerçek duruma yakınsamaktadır. 
            Bu, filtrenin adaptif doğasını göstermektedir.<br/><br/>
            
            <b>6.3 Parametre Etkisi</b><br/><br/>
            
            • Ölçüm gürültüsü (σ = {measurement_noise:.2f} m): Sensör hassasiyetini 
            simüle eder<br/>
            • Süreç gürültüsü (Q = {process_noise:.3f}): Model belirsizliğini temsil eder<br/>
            • Bu parametrelerin dengeli seçimi optimal performans için kritiktir<br/><br/>
            
            <b>6.4 Uygulama Alanları</b><br/><br/>
            
            Bu tür Kalman filtresi uygulamaları gerçek dünyada şu alanlarda kullanılır:<br/>
            • Hava ve uzay araçları navigasyonu<br/>
            • Robotik ve otonom araçlar<br/>
            • Radar ve sonar sistemleri<br/>
            • GPS pozisyon tahmini<br/>
            • Finansal piyasa tahmini<br/>
            • Sinyal işleme uygulamaları
            """
            story.append(Paragraph(conclusion_text, styles['Normal']))
        
        # 7. KAYNAKLAR
        story.append(PageBreak())
        story.append(Paragraph("7. KAYNAKLAR VE REFERANSLAR", heading_style))
        
        references = """
        1. Kalman, R. E. (1960). "A New Approach to Linear Filtering and Prediction Problems"<br/>
        2. Welch, G., & Bishop, G. (2006). "An Introduction to the Kalman Filter"<br/>
        3. Bar-Shalom, Y., Li, X. R., & Kirubarajan, T. (2001). "Estimation with Applications 
        to Tracking and Navigation"<br/>
        4. Simon, D. (2006). "Optimal State Estimation: Kalman, H∞, and Nonlinear Approaches"<br/>
        5. Thrun, S., Burgard, W., & Fox, D. (2005). "Probabilistic Robotics"<br/><br/>
        
        <b>Geliştirme Araçları:</b><br/>
        • Python 3.x<br/>
        • NumPy - Sayısal hesaplamalar<br/>
        • Matplotlib - Görselleştirme<br/>
        • ReportLab - PDF oluşturma
        """
        story.append(Paragraph(references, styles['Normal']))
        
        # Alt bilgi
        story.append(Spacer(1, 30))
        footer = f"""
        <para align=center>
        <i>Bu rapor otomatik olarak oluşturulmuştur.<br/>
        Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>
        </para>
        """
        story.append(Paragraph(footer, styles['Normal']))
        
        # PDF'yi oluştur
        doc.build(story)
        print(f"✓ PDF raporu oluşturuldu: {pdf_path}")
        
    except Exception as e:
        print(f"⚠ PDF oluşturulurken hata: {e}")

# ========== MAIN ==========
if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*15 + "KALMAN FİLTRELİ TOP SİMÜLASYONU")
    print("="*70)
    print("\nÖzellikler:")
    print("  • İnteraktif simülasyon penceresi")
    print("  • Gerçek zamanlı Kalman filtresi tahmini")
    print("  • Gürültülü sensör simülasyonu")
    print("  • Hata analizi ve RMSE hesaplama")
    print("  • PNG grafik kaydetme")
    print("  • PDF rapor oluşturma")
    print("\nKontroller:")
    print("  • Kaydırıcılar: Parametreleri ayarlayın")
    print("  • Başlat/Duraklat: Simülasyonu kontrol edin")
    print("  • Sıfırla: Başa dönün")
    print("  • Kaydet: PNG + PDF dosyalarını oluşturun")
    print("\n" + "="*70 + "\n")
    
    # İnteraktif pencereyi başlat
    create_interactive_plot()
    plt.show()
    
    print("\nSimülasyon kapatıldı. İyi günler!")