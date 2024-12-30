$(document).ready(function() {

    var editor = CodeMirror.fromTextArea(document.getElementById("txt"), {
      mode: {
        name: "python",
        version: 3,
        singleLineStringErrors: false
      },
      lineNumbers: true,
      indentUnit: 4,
      matchBrackets: true,
      lint: true,
      styleActiveLine: true,
      gutters: ["CodeMirror-lint-markers"],
      lintWith: false
    });
  
    $("#run").click(function() {
      // Kullanıcının editördeki kodunu al
      const code = editor.getValue();
  
      // AJAX POST isteği gönder
      $.ajax({
          url: '/submit_code',                     // Sunucu endpoint'i
          method: 'POST',                      // POST yöntemi
          contentType: 'application/json',     // Flask'ın beklediği Content-Type
          data: JSON.stringify({ text: code }), // JSON formatına dönüştür
          success: function(response) {
              print_result(response);          // Başarılı yanıtı işle
          },
          error: function(xhr) {
              // Hata durumunda çıktı göster
              print_result({ error: xhr.responseJSON?.error || "Bir hata oluştu" });
          }
      });
  
      // Çıktıyı göstermek için bir fonksiyon
      function print_result(data) {
          document.getElementById('output').innerHTML = ''; // Önceki çıktıyı temizle
          if (data.error) {
              $("#output").append("<pre style='color: red;'>Hata: " + data.error + "</pre>");
          } else {
              $("#output").append("<pre>" + data.output + "</pre>");
          }
      }
    });
  
    document.getElementById('ai-helper-button').addEventListener('click', function () {
      const txtContent = editor.getValue();
      const outputContent = document.getElementById('output').innerText;
      console.log('txtContent:', txtContent);
      
      // İstek için veri
      const requestData = {
          message: txtContent,  // 'txt' içeriği
          output: outputContent // 'output' içeriği
      };
      
      // API'ye POST isteği yap
      fetch('/api/ai_error_handler', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData),
      })
      .then(response => {
          // Veriyi stream olarak al
          const outputDiv = document.getElementById('ai-output');
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let fullText = '';  // Tüm metni burada birleştireceğiz
          const stream = new ReadableStream({
              start(controller) {
                  function push() {
                      reader.read().then(({ done, value }) => {
                          if (done) {
                              controller.close();
                              outputDiv.innerHTML = `<p>${fullText}</p>`; // Tüm metni ekle
                              return;
                          }
                          // Veriyi al ve 'data:' etiketini kaldırarak birleştir
                          const chunk = decoder.decode(value, { stream: true });
                          fullText += chunk
                          push();
                      });
                  }
                  push();
              }
          });
          return new Response(stream);
      })
      .catch(error => {
          console.error('Hata:', error);
          document.getElementById('ai-output').innerHTML = "<p>Bir hata oluştu.</p>";
      });
    });
  
      document.getElementById("user-icon").addEventListener("click", function () {
          const dropdown = document.getElementById("dropdown-menu");
          dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
      });
  
      document.getElementById("logout").addEventListener("click", async function () {
          const response = await fetch('/logout', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
          });
          if (response.ok) {
              alert("Çıkış yapıldı.");
              window.location.href = "/";
          } else {
              alert("Çıkış yapılamadı.");
          }
      });
  
      // Sayfa dışında bir yere tıklandığında menüyü kapatma
      document.addEventListener("click", function (event) {
          const dropdown = document.getElementById("dropdown-menu");
          const userIcon = document.getElementById("user-icon");
          if (!dropdown.contains(event.target) && !userIcon.contains(event.target)) {
              dropdown.style.display = "none";
          }
      });
  
  });
  
  