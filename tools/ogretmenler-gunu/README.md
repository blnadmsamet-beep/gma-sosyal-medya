# GMA – 24 Kasım Öğretmenler Günü filmi (kurgu hattı)

Dikey 1080×1920, 30 fps Reels filmi. Görseller/seslendirme/müzik ElevenLabs akışında hazır:
**flow_id `fVYIxoqQbmJHSYVJy1qO`** ("GMA – 24 Kasım Öğretmenler Günü filmi").

| Düğüm | node_id | generation_id | Dosya |
|---|---|---|---|
| S1 Kandil | pT18OH61VvqKIITWEr7Z | jt5mkrlRk4Fuhel0eKny | s1.png (1152×2048) |
| S2 Öğretmen ve kandil | n8LWNviUTqznBZmH1EB3 | 5fciNAloh1eEDS2GtJk5 | s2.png |
| S3 Çocuklar ışıkta | tAIhqaQBxHWMOMRBDL9k | 0HkESIgwwfLbhzWYHYfb | s3.png |
| S4 Sabah sınıf | FxfhxZPdayKjBTo4wtIz | wMvQgEmTf1pSEuJ94axH | s4.png |
| S5 Fenerler | ztjlXGweCDR1JThns8sJ | TsIdebmd1InSxbe0HZ7t | s5.png |
| Anlatım (ses FZkK3TvQ0pjyDmT8fzIW, eleven_v4, 29.84 s) | PdGl42Jv1WTZsNXuu1dD | 7e60p7NPDTc6CzoicBWA | narration.mp3 |
| Fon müziği (eleven_music_v2_5, 58 s) | EIJ8l1LkFGGWtnfj5meF | fAsGvsiIciagcFv8ExNk | music.mp3 |

Taze indirme bağlantıları için: `creative_get_generations(flow_id, [generation_id])` → `full_res_url`.

## Kurgu
```
cd tools/ogretmenler-gunu
python3 build.py --images dl/s1.png dl/s2.png dl/s3.png dl/s4.png dl/s5.png \
  --narr dl/narration.mp3 --music dl/music.mp3 --out gma-24kasim-ogretmenler-gunu.mp4
```
- `page.html`: tüm sahneler tek bir deterministik `render(t)` ile çizilir (Ken Burns, kandil ışığı titremesi,
  yazı animasyonları, 24 Kasım kutlama kartı, beyaz zeminde logo kapanışı – reklam serisindeki kapanışla aynı düzen).
- `render.js`: Playwright ile sahne sahne JPEG kare → ffmpeg (sahne başına bir mp4), `-c copy` ile birleştirme.
- `build.py`: anlatımdaki duraklardan cümle zamanlarını çıkarır (9 cümle), sahne/yazı zamanlamasını kurar,
  render eder, anlatım (1 sn gecikmeli) + müziği (sidechain ile kısılan) miksler.
- `assets/logo.png` yoksa `videos/reklam/reklam-05-dort-yonlu-gelisim.mp4` kapanış karesinden otomatik kesilir.
- Gereksinimler: node + playwright (chromium), ffmpeg, python3 + Pillow.

Kontrol: `build.py --test` yalnızca `stills/` altına kontrol kareleri üretir; tam render ~2 dk sürer.
Kareleri kontrol et: yazılar Reels arayüzüne girmemeli (üst 250 px / alt 420 px boş), görsellerde bozuk el/yüz olmamalı;
bozuk görsel varsa aynı düğümü yeniden çalıştır (tek varyasyon).

Anlatım metni:
```
Bir kandil düşünün. Yandıkça kendinden verir; ama odadaki herkes, onun ışığında görür.
Öğretmen, işte o kandildir. Aydınlanacak nesiller için kendinden verir.
Geleceğin Mimarları'nda o ışık, her sabah küçük ellere dokunur.
İlk harfini tanıyan gözlerde… ilk kez "ben yaparım" diyen seslerde…
Bugün, o ışığı taşıyan tüm öğretmenlerimize minnettarız.
24 Kasım Öğretmenler Günü kutlu olsun.
Geleceğin Mimarları Anaokulu. Gelecek için eğitim.
```

Instagram açıklaması önerisi:
```
Öğretmen bir kandil gibidir; aydınlanacak nesiller için kendinden verir.
Tüm öğretmenlerimizin 24 Kasım Öğretmenler Günü kutlu olsun.

📍 Safranbolu · Geleceğin Mimarları Anaokulu
#ÖğretmenlerGünü #24Kasım #GeleceğinMimarları #Safranbolu #anaokulu
```
