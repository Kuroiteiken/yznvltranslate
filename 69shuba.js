(async () => {
    /**
     * Verilen URL'den sayfa içeriğini çeker, metni temizler ve sonraki bölümün URL'sini bulur.
     * @param {string} url - İçeriği çekilecek sayfanın URL'si.
     * @returns {Promise<{text: string|null, nextUrl: string|null}>} - Temizlenmiş metin ve sonraki bölümün URL'si.
     */
    async function getPageContent(url) {
        try {
            const res = await fetch(url);
            if (!res.ok) {
                console.error(`HTTP hatası! Durum: ${res.status}, URL: ${url}`);
                return { text: null, nextUrl: null };
            }

            // === DÜZELTME 1: GBK ENCODING SORUNU ===
            // Metni .text() olarak değil, .arrayBuffer() olarak alıyoruz (ham baytlar)
            const buffer = await res.arrayBuffer();
            // TextDecoder kullanarak 'gbk' kodlamasıyla baytları metne çeviriyoruz.
            const decoder = new TextDecoder('gbk');
            const html = decoder.decode(buffer);
            // === DÜZELTME 1 SONU ===

            const doc = new DOMParser().parseFromString(html, "text/html");

            // Metnin bulunduğu ana alanı ID yerine CLASS ile seçiyoruz.
            const el = doc.querySelector(".txtnav");

            if (!el) {
                console.log("'.txtnav' alanı bulunamadı, bu bölüm atlanıyor.", url);
                // Sonraki linki yine de aramayı deneyebiliriz, belki sayfa yapısı değişmiştir
                const nextLinkOnError = Array.from(doc.querySelectorAll("a"))
                    .find(a => a.textContent.includes("下一章"));
                const nextUrlOnError = nextLinkOnError ? new URL(nextLinkOnError.href, url).href : null;
                return { text: null, nextUrl: nextUrlOnError };
            }

            // Metni temizlemek için elementi klonluyoruz.
            const contentEl = el.cloneNode(true);

            // === İSTENMEYEN ELEMENTLERİ KALDIR ===

            // Başlığı (h1) kaldır
            const title = contentEl.querySelector("h1.hide720");
            if (title) title.remove();

            // Bilgi (tarih/yazar) kısmını kaldır
            const info = contentEl.querySelector(".txtinfo.hide720");
            if (info) info.remove();

            // Sağdaki reklam alanını kaldır
            const adRight = contentEl.querySelector("#txtright");
            if (adRight) adRight.remove();

            // Alttaki reklam alanını kaldır
            const adBottom = contentEl.querySelector(".bottom-ad");
            if (adBottom) adBottom.remove();

            // Metin içindeki ".contentadv" reklamlarını kaldır (HTML'de görüldü)
            const contentAds = contentEl.querySelectorAll(".contentadv");
            contentAds.forEach(ad => ad.remove());

            // === TEMİZ METNİ AL ===

            // Kalan elementlerin metnini al (innerText, <br> etiketlerini korur)
            const text = contentEl.innerText.trim();

            // === DÜZELTME 2: SONRAKİ SAYFA SEÇİCİSİ ===
            // Daha spesifik bir seçici kullanarak doğru linki buluyoruz (.page1 içindeki son <a> etiketi)
            const nextLink = doc.querySelector(".page1 a:last-child");
            let nextUrl = null;

            // Linkin gerçekten "sonraki bölüm" linki olduğunu kontrol et
            if (nextLink && nextLink.textContent.includes("下一章")) {
                nextUrl = new URL(nextLink.href, url).href;

                // Son sayfa linkleri bazen 'javascript:;' olabilir, bunu kontrol et
                if (nextUrl.includes('javascript:;')) {
                    nextUrl = null;
                }
            }
            // === DÜZELTME 2 SONU ===

            return { text, nextUrl };

        } catch (error) {
            console.error(`Hata oluştu (${url}):`, error);
            return { text: null, nextUrl: null }; // Hata durumunda dur
        }
    }

    let url = location.href;
    let counter = 0;
    let allText = "";
    let emtyText = "";

    while (url) {
        counter++;
        console.log(`📄 ${counter}. bölüm alınıyor: ${url}`);

        const { text, nextUrl } = await getPageContent(url);

        if (text) {
            // Bölüm başlığı ve içerik ekle
            allText += `## Bölüm - ${counter} ##\n\n${text}\n\n`;
        } else {
            console.log(`⚠ ${counter}. bölüm için içerik alınamadı veya içerik boş.`);
            allText += `## Bölüm - ${counter} ##\n\nEksik Bölüm\n\nBölüm Sonu${counter}\n\n`;
            emtyText += `## Bölüm - ${counter} ##\n\n`;
        }

        if (!nextUrl) {
            console.log("✅ Son bölüme ulaşıldı!");
            break;
        }

        // Örnek: Belirli bir bölümde durdurma (isteğe bağlı)
        /*
        if (counter == 5) {
            console.log("✅ Manuel olarak 10. bölümde durduruldu.")
            break;
        }
        */

        url = nextUrl;
        // Sunucuyu yormamak için bekleme süresini biraz artıralım
        await new Promise(r => setTimeout(r, 2000));
    }

    if (allText.length === 0) {
        console.log("Hiçbir bölümden metin alınamadı. Dosya oluşturulmuyor.");
        return;
    }

    // Tek büyük TXT dosyası olarak indir
    const blob = new Blob([allText], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);

    // Kitap adını almaya çalış (opsiyonel)
    let bookTitle = document.title.split('-')[0] || "tum_bolumler";
    link.download = `${bookTitle.trim()}.txt`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log(`🏁 Tüm bölümler indirildi ve '${link.download}' olarak kaydedildi!`);
    if (emtyText) {
        console.log('⚠ Boş Bölüm Listesi:');
        console.log(emtyText);
    } else {
        console.log('Eksik Bölüm Yok✅')
    }
})();

