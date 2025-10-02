import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

# Fizik parametreleri
g = 9.8  # Yerçekimi ivmesi (m/s²)
v0 = 50  # Başlangıç hızı (m/s)
angle = 45  # Fırlatma açısı (derece)
dt = 0.02  # Zaman adımı (saniye)
e = 0.7  # Geri tepme katsayısı (enerji kaybı)

# Başlangıç değerleri
def initialize_motion(v0, angle):
    angle_rad = np.radians(angle)
    vx = v0 * np.cos(angle_rad)
    vy = v0 * np.sin(angle_rad)
    return vx, vy, 0, 0, 0  # vx, vy, x, y, t

# Simülasyon verileri
vx, vy, x, y, t = initialize_motion(v0, angle)
x_data, y_data = [x], [y]
is_running = False

# Grafik oluşturma
fig, ax = plt.subplots(figsize=(12, 8))
plt.subplots_adjust(left=0.1, bottom=0.35)

ax.set_xlim(0, 300)
ax.set_ylim(0, 150)
ax.set_xlabel('Mesafe (m)', fontsize=12)
ax.set_ylabel('Yükseklik (m)', fontsize=12)
ax.set_title('2D Top Yörüngesi Simülasyonu', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.axhline(y=0, color='green', linewidth=2, label='Zemin')

# Çizim elemanları
line, = ax.plot([], [], 'b-', linewidth=2, label='Yörünge')
ball, = ax.plot([], [], 'ro', markersize=15, label='Top')
text_info = ax.text(0.02, 0.95, '', transform=ax.transAxes, 
                    verticalalignment='top', fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
ax.legend(loc='upper right')

# Kaydırıcılar (Sliders)
ax_v0 = plt.axes([0.2, 0.20, 0.65, 0.03])
ax_angle = plt.axes([0.2, 0.15, 0.65, 0.03])
ax_gravity = plt.axes([0.2, 0.10, 0.65, 0.03])

slider_v0 = Slider(ax_v0, 'Hız (m/s)', 10, 100, valinit=v0, valstep=1)
slider_angle = Slider(ax_angle, 'Açı (°)', 0, 90, valinit=angle, valstep=1)
slider_gravity = Slider(ax_gravity, 'Yerçekimi (m/s²)', 1, 20, valinit=g, valstep=0.1)

# Butonlar
ax_start = plt.axes([0.3, 0.025, 0.15, 0.04])
ax_reset = plt.axes([0.55, 0.025, 0.15, 0.04])
btn_start = Button(ax_start, 'Başlat/Duraklat')
btn_reset = Button(ax_reset, 'Sıfırla')

def update_params(val):
    global v0, angle, g, is_running
    if not is_running:
        v0 = slider_v0.val
        angle = slider_angle.val
        g = slider_gravity.val
        reset_simulation()

slider_v0.on_changed(update_params)
slider_angle.on_changed(update_params)
slider_gravity.on_changed(update_params)

def reset_simulation():
    global x, y, vx, vy, t, x_data, y_data
    vx, vy, x, y, t = initialize_motion(v0, angle)
    x_data, y_data = [x], [y]
    line.set_data([], [])
    ball.set_data([], [])
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
    global x, y, vx, vy, t, x_data, y_data
    
    if not is_running:
        return line, ball, text_info
    
    # Fizik hesaplamaları
    vy -= g * dt
    x += vx * dt
    y += vy * dt
    t += dt
    
    # Yere çarpma kontrolü
    if y < 0:
        y = 0
        vy = -vy * e  # Zıplama (enerji kaybı)
        if abs(vy) < 0.5:  # Çok küçük hız varsa dur
            vy = 0
    
    # Veri kaydetme
    x_data.append(x)
    y_data.append(y)
    
    # Grafik sınırlarını güncelle
    if x > ax.get_xlim()[1] - 20:
        ax.set_xlim(0, x + 50)
    
    # Çizim güncelleme
    line.set_data(x_data, y_data)
    ball.set_data([x], [y])
    
    # Bilgi metni
    info_text = f'Zaman: {t:.2f} s\n'
    info_text += f'Pozisyon: ({x:.1f}, {y:.1f}) m\n'
    info_text += f'Hız: ({vx:.1f}, {vy:.1f}) m/s\n'
    info_text += f'Toplam Hız: {np.sqrt(vx**2 + vy**2):.1f} m/s'
    text_info.set_text(info_text)
    
    return line, ball, text_info

# Animasyon
ani = FuncAnimation(fig, animate, interval=20, blit=True, cache_frame_data=False)
ani.event_source.stop()  # Başlangıçta durdur

plt.show()