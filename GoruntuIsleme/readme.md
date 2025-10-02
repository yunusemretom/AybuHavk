
# 🧠 YOLOv8 ile Görüntü İşleme

Merhaba! 👋 Bugün YOLOv8 kullanarak görüntü işleme dünyasına adım atıyoruz. Hazırsanız başlayalım 🚀

---

## 📂 Veri Seti Hazırlama

Bir cihazın etrafındaki nesneleri tanıyabilmesi için önce ona **neyi algılaması gerektiğini öğretmemiz** gerekir. Tıpkı bir çocuğa çevreyi tanıtırken gördüğü nesnelerin adını söylememiz gibi 👶➡️🖼️.
Bizim cihazımız da “çocuğumuz” ve biz ona hem şekilleri **gösterecek** hem de **isimlerini öğreteceğiz**. İşte bu sürece **veri seti** diyoruz.

👉 Ne kadar çok ve çeşitli veri sağlarsak, modelimiz o kadar iyi öğrenir.
Ama dikkat ⚠️:
Eğer sadece **tek tip** örnek gösterirsek model her şeyi o nesne sanabilir. Bu duruma **overfitting (aşırı öğrenme)** denir.
Bunu önlemek için:

* Farklı örnekler
* Farklı ortam ve ışık koşulları
* Az da olsa boş görseller kullanmalıyız.

---

## 🛠️ Train / Valid / Test Ayrımı

Veri seti hazırlanırken üç farklı kısım oluşturulur:

* **Train** 🏋️ → Modelin öğrendiği kısım.
* **Valid** 📊 → Eğitim sırasında ara sınav gibidir. Modelin doğru yolda olup olmadığını buradan görürüz.
* **Test** 🧪 → Eğitim bittikten sonra, modelin hiç görmediği verilerle yapılan nihai sınavdır. Olmasa da olur ama performansı ölçmek için faydalıdır.

---

## ✈️ Örnek: Uçak Eğitimi

Eğer uçak algılayan bir model eğitiyorsak:

* Sadece **tek tip** uçak resmi koymak yeterli olmaz.
* Loş ışık, güneşli hava, farklı kamera açıları gibi çeşitli koşullarda da resimler eklenmelidir 🌞🌙💡.
* Böylece model farklı koşullarda da yüksek doğrulukla çalışır.
* Ayrıca veri setine birkaç **boş resim** eklemek, modelin her karede uçak aramamasını öğretir.

---

## 🎯 Sonuç

Kısaca:

* Çeşitli ve dengeli bir veri seti hazırla.
* Train/Valid/Test ayrımına dikkat et.
* Overfitting’i önlemek için farklı senaryoları modele tanıt.

Eğer bu adımları dikkatlice uygularsanız güzel sonuçlar elde edebilirsiniz 💯.

🛠️ Denemekten korkmayın, modelinizi geliştirdikçe daha iyi sonuçlar alacaksınız.
Herkese iyi çalışmalar dileriz! 🙌

