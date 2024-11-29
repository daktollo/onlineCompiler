// Created by Ethan Chiu 2016
// Updated August 4, 2018

$(document).ready(function() {
  //Pulls info from AJAX call and sends it off to codemirror's update linting
  //Has callback result_cb
  var socket = io.connect('http://' + document.domain + ':' + location.port + '/check_disconnect');
  var click_count = 0;

  // Hataları işleme ve tabloyu güncelleme
  function check_syntax(code, result_cb) {
    //Example error for guideline
    var error_list = [{
      line_no: null,
      column_no_start: null,
      column_no_stop: null,
      fragment: null,
      message: null,
      severity: null
    }];
  
      //Push and replace errors
      function check(data) {
        //Clear array.
        error_list = [{
          line_no: null,
          column_no_start: null,
          column_no_stop: null,
          fragment: null,
          message: null,
          severity: null
        }];
        document.getElementById('errorslist').innerHTML = '';
        //Check if pylint output is empty.
        if (data == null) {
          result_cb(error_list);
        } else {
          $('#errorslist').append("<tr>" + "<th>Line</th>" + "<th>Severity</th>" +
            "<th>Error</th>" + "<th>Tips</th>" +
            "<th>Error Code</th>" +
            "<th>Error Info</th>" + "</tr>");
          var data_length = 0;
          if (data != null) {
            data_length = Object.keys(data).length;
          }
          for (var x = 0; x < data_length; x += 1) {
            if (data[x] == null) {
              continue
            }
            number = data[x].line
            code = data[x].code
            codeinfo = data[x].error_info
            severity = code[0]
            moreinfo = data[x].message
            message = data[x].error
  
            //Set severity to necessary parameters
            if (severity == "E" || severity == "e") {
              severity = "error";
              severity_color = "red";
            } else if (severity == "W" || severity == "w") {
              severity = "warning";
              severity_color = "yellow";
            }
            //Push to error list
            error_list.push({
              line_no: number,
              column_no_start: null,
              column_no_stop: null,
              fragment: null,
              message: message,
              severity: severity
            });
  
            //Get help message for each id
            // var moreinfo = getHelp(id);
            //Append all data to table
            $('#errorslist').append("<tr>" + "<td>" + number + "</td>" +
              "<td style=\"background-color:" + severity_color + ";\"" +
              ">" + severity + "</td>" +
              "<td>" + message + "</td>" +
              "<td>" + moreinfo + "</td>" +
              "<td>" + code + "</td>" +
              "<td>" + codeinfo + "</td>" +
              "</tr>");
          }
          result_cb(error_list);
        }
  
      }
      //AJAX call to pylint
      $.post('/check_code', {
        text: code
      }, function(data) {
        current_text = data;
        console.log("current_text:", current_text)
        check(current_text);
        return false;
      }, 'json');
  }
  


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
    lintWith: {
      "getAnnotations": CodeMirror.remoteValidator,
      "async": true,
      "check_cb": check_syntax
    },
  });

  //Actually Run in Python
  $("#run").click(function() {
    console.log("run func")
    $.post('/run_code', {
      text: editor.getValue()
    }, function(data) {
      print_result(data);
      return false;
    }, 'json');

    function print_result(data) {
      document.getElementById('output').innerHTML = '';
      $("#output").append("<pre>" + data + "</pre>");
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
});
