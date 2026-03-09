(async () => {
    /**
     * Verilen URL'den sayfa içeriğini çeker, metni temizler ve sonraki bölümün URL'sini bulur.
     * Dikkat önemli!!! 112. satıra son bölüm numarası yazılacak. Son bölüme gelindiğinde durması için bir sınır koyuyoruz.
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

            // === DÜZELTME 1: KORECE ENCODING (UTF-8) ===
            const html = await res.text();
            // === DÜZELTME 1 SONU ===

            const doc = new DOMParser().parseFromString(html, "text/html");

            // === DÜZELTME 2: İÇERİK SEÇİCİSİ ===
            const el = doc.querySelector("#novel_content"); 
            
            if (!el) {
                console.log("'#novel_content' alanı bulunamadı, bu bölüm atlanıyor.", url);
                const nextLinkOnError = doc.querySelector("#goNextBtn");
                const nextUrlOnError = (nextLinkOnError && nextLinkOnError.href) ? new URL(nextLinkOnError.href, url).href : null;
                return { text: null, nextUrl: nextUrlOnError };
            }

            // Metni temizlemek için elementi klonluyoruz.
            const contentEl = el.cloneNode(true);

            // === İSTENMEYEN ELEMENTLERİ KALDIR ===
            
            // Varsa resimlerin bulunduğu div'i kaldır (.view-img)
            const viewImg = contentEl.querySelector(".view-img");
            if (viewImg) viewImg.remove();
            
            // Başlığı (h1) kaldır
            const title = contentEl.querySelector("h1");
            if (title) title.remove();

            // *** ayıracı gibi stil div'lerini kaldır
            const dividers = contentEl.querySelectorAll('div[style*="text-align:center"]');
            dividers.forEach(d => d.remove());
            
            // === DÜZELTME 4: <p> ETİKETLERİ İÇİN SATIR ATLAMASI ===
            // .innerText.trim() kullanmak yerine, kalan tüm <p> etiketlerini buluyoruz.
            const paragraphs = contentEl.querySelectorAll("p");
            
            let textLines = []; // Her bir paragraf metnini tutacak bir dizi
            
            paragraphs.forEach(p => {
                const pText = p.innerText.trim();
                if (pText) { // Boş <p> etiketlerini atla
                    textLines.push(pText);
                }
            });
            
            // Tüm satırları, aralarında birer yeni satır (\n) olacak şekilde birleştir
            const text = textLines.join("\n");
            // === DÜZELTME 4 SONU ===

            // === DÜZELTME 3: SONRAKİ SAYFA SEÇİCİSİ ===
            const nextLink = doc.querySelector("#goNextBtn");
            let nextUrl = null;
            
            if (nextLink && nextLink.href) {
                 nextUrl = new URL(nextLink.href, url).href;
                 
                 if (nextUrl.includes('javascript:;') || nextUrl === url) {
                     nextUrl = null;
                 }
            }
            // === DÜZELTME 3 SONU ===

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
        //Manuel olarak belirlenecek. Son bölüme gelindiğinde durması için bir sınır koyuyoruz. Son Bölüm numarası yazılacak.
        if (counter>= 120){
            console.log(`✅ ${counter} . bölüme ulaşıldı!`);
            break;
        }
        url = nextUrl;
        // Sunucuyu yormamak için bekleme
        await new Promise(r => setTimeout(r, 10000)); 
    }

    if (allText.length === 0) {
        console.log("Hiçbir bölümden metin alınamadı. Dosya oluşturulmuyor.");
        return;
    }

    // Tek büyük TXT dosyası olarak indir
    const blob = new Blob([allText], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    
    // Kitap adını almaya çalış (Örn: "야구단 신입이 너무 잘함 703화 > 북토끼..." -> "야구단 신입이 너무 잘함")
    let bookTitle = document.title.split('>')[0].trim() || "tum_bolumler";
    bookTitle = bookTitle.replace(/\s*\d+화$/, "").trim(); // " 703화" gibi bölüm numarasını kaldır
    
    link.download = `${bookTitle || 'tum_bolumler'}.txt`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    console.log(`🏁 Tüm bölümler indirildi ve '${link.download}' olarak kaydedildi!`);
    if(emtyText){
        console.log('⚠ Boş Bölüm Listesi:');
        console.log(emtyText);
    }else{
        console.log('Eksik Bölüm Yok✅')
    }
    
})();