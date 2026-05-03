# Bugün Kayıt Playbook (text-overlay tarzı)

> Tarih: 2026-04-26
> Strateji: sessiz kayıt + post-edit text overlay
> Toplam ham kayıt: ~20-25 dk, 11 scene
> Final video: 60-90 sn (uzun beklemeler post'ta hızlandırılır)

## Pre-flight checklist (kayıttan ÖNCE, 5 dk)

### OBS Studio config
- Settings → Video → Base + Output: **1920×1080**, FPS **30**
- Settings → Output → Recording Path: temiz bir klasör (ör. `Desktop/recordings/`)
- Settings → Output → Recording Format: **MKV** (crash olursa korumalı)
- Settings → Audio → mic + desktop ses **kapalı** (sessiz kayıt yapıyoruz)
- Source: **Window Capture** → Windows Terminal (WSL'in açık olduğu)

### WSL terminal hazırlığı
- **Windows Terminal**, full-screen civarı, koyu tema
- Font: video okunabilirliği için büyütülsün (ör. Cascadia Mono **16pt**)
- WSL Ubuntu-22.04 aç
- Pre-flight komutlar:
  ```bash
  cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
  bash scripts/install_skill.sh      # son SKILL.md sync
  export PATH="$HOME/.local/bin:$PATH"
  ```
- **Henüz hermes'i başlatma** — soğuk başlangıcı kameraya almak istiyoruz (`Initializing agent...` satırı demoya dahil).

### Tarayıcı hazırlığı (Scene 10 için ayrı pencere)
- **Firefox veya Chrome** taze pencere (extension görünmesin, yalnız ihtiyacımız olan tab açık)
- `https://hermes-comic-neon-and-ash.pages.dev` URL'i bookmark veya pre-load
- Mobil görünüm için: Chrome → DevTools (F12) → Toggle Device Toolbar → **iPhone 14 Pro** preset

### Workspace seçimi
- **Tavsiye edilen:** taze yeni seri kaydet (~$2 maliyet) — daha autentik "live demo"
- **Kısayol:** mevcut `neon-and-ash` workspace'i Scene 10'da kullan (zaten yayında)
- Scene 1-6'da yeni seri üretirsin (ör. "zaman-tamircisi") — yolculuğu kaydeder

## Kayıt akışı — scene scene

> **OBS hotkey ipucu:** Settings'ten **F9 = Start/Stop Recording** ata, tıklamaktan iyi.

> **Adlandırma:** her scene'i `scene_<NN>_<slug>.mkv` olarak kaydet. Hata olursa sadece o scene'i tekrar al.

> **Caption işaretleri:** 💬 = post'ta caption gerekiyor / 📌 = bu anı hızlandırma, kritik

---

### 🎬 Scene 1 — Hermes açılış + skill çağrısı (~30 sn ham)

**Hedef:** Bunun bir Hermes Agent skill'i olduğunu, slash komutla çağrıldığını göster.

1. **Kayıt başlat** (F9)
2. Terminal'e yaz:
   ```
   uv run hermes
   ```
   Enter. Hermes ASCII banner'ının tamamen render olmasını bekle.
3. Banner görünür olduğunda ("1 skill" rozeti varsa install_skill çalışmış demektir), yaz:
   ```
   /comic-series Bana gezgin bir saatçi hakkında manga yap. Saatçi zamanı tamir ediyor, gölgeler onu durdurmaya çalışıyor.
   ```
   Enter.
4. `⚡ Loading skill: comic-series` ve sistem activation note (`+220 lines`) çıkmasını bekle.
5. **Kayıt durdur** Hermes ilk mesajına başladığında.

**Post'ta eklenecek caption'lar:**
- 💬 Banner'da: **`Hermes Agent — 1 skill loaded`**
- 💬 Skill yüklenince: **`/comic-series — playbook activated`**

---

### 🎬 Scene 2 — Stage 1 propose (3 framing) (~90 sn ham)

**Hedef:** "AI önce 3 yaratıcı yön öneriyor, sonra ilerliyor."

1. **Kayıt başlat** (aynı hermes oturumu, restart yok)
2. Hermes `uv run comic series propose "..."` çalıştıracak. ~50-60 sn bekle.
3. 3 framing başlık + tagline + paragraf ile ekrana akacak.
4. **Kayıt durdur** 3'ü görünür + en altta "pick one" prompt geldiğinde.

**Caption'lar:**
- 📌 Bekleme sırasında (~50sn): post'ta 4x hızlandır; overlay **`Kimi K2.5 — 3 framings (50s)`**
- 💬 Framing'ler çıkarken: **`Genuinely different tones — your choice`**
- 💬 Bir tagline'ı vurgu ile (ör. "Dünyayı sarıyor ki dönüş sun") **call-out arrow + ✨**

---

### 🎬 Scene 3 — Pick + Stage 2 canon (~3 dk ham)

**Hedef:** Tek seçimden Kimi'nin tam seri bible'ı üretmesi.

1. **Kayıt başlat**
2. Yaz:
   ```
   2
   ```
   Enter. (Option 2 = cosmic / mythic — visual showcase için en güçlü.)
3. Hermes `comic series new "..."` çalıştırır → ~2-3 dk Kimi K2.5 canon üretirken bekle.
4. Tamamlanınca Hermes `read_file` ile 4 canon dokümanı okur ve temiz bullet özet yazar.
5. **Kayıt durdur** özet görünür + onay prompt çıktığında.

**Caption'lar:**
- 📌 Kimi beklerken: post'ta 4-8x hızlandır; overlay **`Kimi K2.5 — generating world + characters + style (180s)`**
- 💬 Canon dosyaları yazılırken: **`4 canon files persisted`**
- 💬 Özet görününce: **`Series bible — ready`**

---

### 🎬 Scene 4 — Stage 3 character propose (~90 sn ham)

**Hedef:** Karakter arketip önerileri.

1. **Kayıt başlat**
2. Yaz:
   ```
   kabul ediyorum devam et
   ```
   Enter.
3. Hermes `comic character propose "..."` çalıştırır. ~50 sn.
4. 3 arketip çıkar (ör. Sakristan / Gladyatör / Hurdacı).
5. **Kayıt durdur** pick prompt'ta.

**Caption'lar:**
- 💬 Arketipler çıkarken: **`Character design — 3 distinct archetypes`**
- 💬 Her arketipte bir özelliği highlight: ör. **`Cyberpunk warrior →`**, **`Surreal patchwork →`**

---

### 🎬 Scene 5 — Reference gen + script self-patch 🌟 ALTIN AN (~3-4 dk ham)

**Hedef:** "AI kendi tooling'ini debug ediyor" flagship momenti.

1. **Kayıt başlat**
2. Yaz:
   ```
   2
   ```
   Enter. (Option 2 = warrior arketip.)
3. Hermes `gen_references.py`'i yanlış flag'lerle çağırır → hata.
4. Hermes script'i `read_file` ile inceler.
5. Hermes `patch` tool ile yeni karakter setini ekler → diff ekranda görünür.
6. Hermes `gen_references.py --set <slug>` ile tekrar çalıştırır → ~100 sn 9 candidate üretir.
7. **Kayıt durdur** candidate'lar listelenip Windows path görününce.

**Caption'lar:**
- 💬 İlk hatada: **`Tool encounters unknown character — won't fall back to hallucination`**
- 💬 Hermes script'i okurken: **`Hermes inspects its own pipeline`**
- 💬 Patch diff sırasında: **`Adds new character set to gen_references.py`** (sparkle icon)
- 💬 Retry'da: **`Self-patched. Retrying.`**
- 💬 Tamamlanınca: **`9 candidate references — pick your hero`**

---

### 🎬 Scene 6 — Reference pick + Chapter 1 (~5-7 dk ham)

**Hedef:** Tek chapter'ı uçtan uca üret. "Render cascade" görsel zirve.

1. **Kayıt başlat**
2. Yaz:
   ```
   Portre: 2, Tam vücut: 1, Aksiyon: 3
   ```
   Enter.
3. Hermes ref'leri kopyalar.
4. Yaz:
   ```
   ilk chapter için bir beat öner, --panels 8 ile yap
   ```
   Enter.
5. 3 chapter beat çıkmasını bekle.
6. Yaz:
   ```
   1
   ```
   Enter. Hermes `comic chapter new "..." --panels 8` çalıştırır. ~2 dk.
7. Yaz:
   ```
   evet render et
   ```
   Hermes `comic chapter render 1 --seed 42 --concurrency 5` çalıştırır. 8 panel için ~2-3 dk.
8. **Kayıt durdur** chapter.png path görünüp Windows path yazıldığında.

**Caption'lar:**
- 📌 Render sırasında: 8x hızlandır; overlay **`fal.ai Flux Kontext + Manhwa LoRA — 8 panels in parallel`**
- 💬 Progress bar görününce: **`Live progress — 5 parallel workers`**
- 💬 Tamamlanınca: **`Chapter 1 rendered. Webtoon stitched. 25 sec.`**

> Eğer burada bir şey kırılırsa, dur, benimle debug yap, sadece bu scene'i tekrar kaydet.

---

### 🎬 Scene 7 — Multimodal Continuity Guardian 🌟 KIMI FLAGSHIP (~90 sn ham)

**Hedef:** Kimi K2.5 multimodal showcase — görselleri görüp tutarsızlık flag'lemesi.

> **Kısayol:** Chapter 2 üretmeden (~5 dk tasarruf), mevcut `neon-and-ash` workspace'in Chapter 2 continuity check'ini kullan. **İKİNCİ terminal aç:**

```bash
cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"
export PATH="$HOME/.local/bin:$PATH"
uv run comic chapter continuity 2 --multimodal
```

1. **Kayıt başlat** bu ikinci terminalde
2. Yukarıdaki komutu çalıştır
3. Kimi K2.5 multimodal işlemesi için ~60 sn bekle (önceki chapter image'ları + yeni spec'i alıyor)
4. Continuity raporu çıkar — 6 issue listelenir (Crown drift, cape rengi, blade el, vb.)
5. **Kayıt durdur** uyarılar listesi tam görünür olduğunda.

**Caption'lar:**
- 💬 Çalıştırmadan önce: **`Multimodal continuity guardian — Kimi K2.5 sees previous panels + canon`**
- 💬 Bir uyarıyı highlight: ör. **`Caught: motorcycle headlamp color mismatch (Ch1 magenta vs Ch2 cyan)`** ok ile
- 💬 Outro: **`Visual + textual reasoning — irreplaceable`**

---

### 🎬 Scene 8 — Style evolution + chapter 3 (~3-4 dk ham)

**Hedef:** "Skill'ler feedback ile evriliyor" göster.

> **Aynı kısayol — neon-and-ash workspace.**

1. **Kayıt başlat**
2. Terminal'de:
   ```bash
   uv run comic chapter feedback "more cinematic silence: max 1 bubble per panel, mandatory wordless transitions, action panels ≥70% canvas"
   ```
3. Patch özetini + history snapshot path'i göster.
4. (Opsiyonel: editor'da `~/.hermes/skills/comic-series/scripts/style_evolve.py` ve `style-card.md` v1.1 diff'ini kısaca aç.)
5. Çalıştır:
   ```bash
   ls workspaces/neon-and-ash/chapters/03/chapter.png
   ```
   Ve o dosyayı (Windows Explorer'dan) aç — Chapter 3'ün evrilmiş silent-beat layout'unu göster.
6. **Kayıt durdur** görsel farkı gösterdikten sonra.

**Caption'lar:**
- 💬 Feedback'te: **`User feedback → AI patches the skill file itself`**
- 💬 Diff göster (post'ta): **`v1.0 → v1.1: silence rules added`**
- 💬 Chapter 3 image'da: **`Next chapter rendered with the new style`** (daha az bubble'a ok)

---

### 🎬 Scene 9 — Publish + canlı URL (~60 sn ham)

**Hedef:** Kapanış. Tool gerçek URL'e tek komutla publish ediyor.

> Scene 1-6'dan üreteceğin yeni serini kullan (Chapter 1 kırıldıysa neon-and-ash).

1. **Kayıt başlat**
2. Hermes (veya terminal):
   ```bash
   uv run comic series cover --tagline "Across dying dimensions, a watchmaker mends the fraying fabric of time."
   uv run comic series export
   uv run comic series publish --provider both
   ```
3. Göster: cover üretimi → export → CF deploy log → Surge deploy log → temiz ✅ block'unda iki URL.
4. **Kayıt durdur** success block'ta.

**Caption'lar:**
- 💬 Cover'da: **`1200×630 poster — Twitter card ready`**
- 💬 Deploy'da: **`Cloudflare primary + Surge fallback`**
- 💬 URL output'ta: **URL'i glow box ile vurgula**

---

### 🎬 Scene 10 — Tarayıcı turu + share button 🌟 FİNAL (~60 sn ham)

**Hedef:** Gerçek kullanıcılar publish edilmiş webtoon'u deneyimliyor.

1. **Kayıt başlat** (artık tarayıcı penceresi)
2. Publish edilmiş URL'i Firefox/Chrome'da aç (Scene 9'dan, veya `https://hermes-comic-neon-and-ash.pages.dev`)
3. **Cover hero'yu göster** (1.5 sn)
4. **Yavaş scroll** Chapter 1'de — karakter consistency'sini göster
5. **Hızlı scroll** Chapter 2 + 3 (uzunluğu göster)
6. **Aşağıya scroll** — "Enjoyed it?" + büyük Share on X butonu görünsün
7. **Share on X tıkla** — yeni tab'da pre-filled tweet açılır
8. **Tweet içeriğini göster** — 4 @mention + hashtag + URL görünür. Tweet butonuna hover ama postlamadan dur.
9. **Kayıt durdur**.

**Caption'lar:**
- 💬 Hero'da: **`Live mobile-first webtoon — anyone can read`**
- 💬 Scroll sırasında: **`Character consistency across 3 chapters`**
- 💬 Share button'da: **`One-click share — pre-filled tweet`**
- 💬 Tweet preview'da: **@NousResearch · @Teknium · @Kimi_Moonshot · @Knkchn0** sparkle ile vurgula

---

### 🎬 Scene 11 (BONUS) — `comic auto` showcase (~3 dk ham)

**Hedef:** Opsiyonel B-roll. Non-interactive showcase modu.

1. **Kayıt başlat** (taze terminal)
2. Çalıştır:
   ```bash
   uv run comic auto "A lighthouse keeper who collects dying stars in glass bottles" --chapters 1 --panels 4 --no-publish --no-cover
   ```
3. Cascade'i göster: Stage 1 propose → Stage 2 canon → Stage 4 render → ~3 dk'da done.
4. **Kayıt durdur** "🎬 COMPLETE" mesajında.

**Caption'lar:**
- 💬 Başlangıçta: **`comic auto — full pipeline, single command`**
- 💬 Sonda: **`From premise to webtoon. Hands-off.`**

---

## Post-edit planı (kaydı bitirdikten sonra)

Bana TÜM `.mkv` dosyalarını gönder. Ben:
1. 60-90 saniyelik story arc'a kes (Scene 1, 5 [self-patch], 7 [multimodal], 9 [publish], 10 [share] focus)
2. Her 💬 işaretine text overlay ekle (İngilizce caption, temiz sans-serif font)
3. Uzun beklemeleri hızlandır (📌 işaretleri → 4-8x)
4. En başa 3 saniyelik hook ekle (rapid Neon & Ash scroll + title reveal)
5. Renk uyumlandırma (hafif magenta/cyan boost, brand palette ile)
6. Minimal SFX (sade transition'lar; v1'de müzik yok — sonra Pixabay track ekleyebiliriz)
7. 1920×1080 H.264 MP4 export, <50 MB Twitter-safe

V1 sonrası opsiyonel:
- Music bed (Pixabay royalty-free, low-key cinematic)
- Mobil-vertical 9:16 cut (X / Threads / IG için)
- Twitter thread breakdown (3-4 tweet, her biri 30 sn'lik klip)

## Kritik hatırlatmalar

- **Scene 1-6 arası `hermes`'i kapatma.** Aynı oturum = aynı bağlam.
- **CLI bir komutta hata verirse:** kaydı durdur, bana bildir, ben düzeltirim, sadece o scene'i tekrar kaydet.
- **Scene'leri anında bir klasöre kaydet** ve OneDrive/cloud'a yedekle (toplam max 5 GB — rahat sığar).
- **Önce TEK SCENE test et** her şeyi kaydetmeden — Scene 1'i kaydet, bana gönder, OBS quality + frame'i onaylarım, sonra Scene 2-11 devam.

## Hızlı başlangıç sırası

1. OBS setup (5 dk)
2. Windows Terminal aç, yukarıdaki pre-flight komutları çalıştır (kayıt yok)
3. **Scene 1'i kalite kontrolü olarak kaydet**
4. Bana dosyayı (veya screenshot) gönder
5. Kalite OK ise → Scene 2-11 devam
6. Hepsi bittiğinde gönder

## Bütçe hatırlatma

- Live recording API harcaması: Scene 1-6 fresh series için ~$2-3
- Cover üretimi: ~$0.04
- Multimodal continuity check: ~$0.03
- `comic auto` smoke: ~$0.25
- **Toplam recording session bütçesi: ~$3-4** / kalan $20+ bütçeden ✓

Standby'da olacağım — scene'ler arası bir şey ters gözükürse hemen bildir.
