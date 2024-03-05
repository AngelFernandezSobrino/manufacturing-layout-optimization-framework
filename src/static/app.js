function request() {
    console.log("Send function request");



    postData("/run", window.editor.getValue()).then((data) => {
        console.log(data); // JSON data parsed by `data.json()` call

        document.querySelector("#container").style.height = "70%"

        let resultsNode = document.querySelector("#result")
        let table = document.createElement("table")
        resultsNode.appendChild(table)

        let thead = document.createElement("thead")
        table.appendChild(thead)
        let tr = document.createElement("tr")
        thead.appendChild(tr)
        data.forEach((row, row_index) => {
            let th = document.createElement("th")
            th.innerText = "Cell " + row_index
            th.style.width = "100px"
            tr.appendChild(th)
        });

        let tbody = document.createElement("tbody")
        table.appendChild(tbody)

        data.forEach((row, row_index) => {

            let tr = document.createElement("tr")

            tr.style.height = "40px"
            tr.style.borderWidth = "1px"
            tr.style.borderStyle = "solid"
            tr.style.borderColor = "grey"
            tbody.appendChild(tr)

            row.forEach((cell, column_index) => {

                let td = document.createElement("td")

                td.id = `${column_index}-${row_index}`
                td.style.width = "100px"
                td.style.height = "100%"
                td.style.borderWidth = "0 2px 0 0"
                td.style.borderStyle = "solid"
                td.style.borderColor = "grey"
                td.style.width = "100px"
                td.innerText = cell
                tr.appendChild(td)
            })

        });

    });
}

async function postData(url = "", data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        mode: "cors", // no-cors, *cors, same-origin
        credentials: "same-origin", // include, *same-origin, omit
        headers: {
            "Content-Type": "application/yaml"
        },
        redirect: "follow", // manual, *follow, error
        referrerPolicy: "no-referrer", // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: data, // body data type must match "Content-Type" header
    });
    return response.json(); // parses JSON response into native JavaScript objects
}


function loadSampleModel() {
    (async () => {

        console.log("Loading sample model")
        result = await fetch("/static/sample_model.yaml");
        content = await result.text();

        let model = monaco.editor.createModel(content)

        monaco.editor.setModelLanguage(model, "yaml")

        window.editor.setModel(model)

    })()
}

function downloadModel() {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/yaml;charset=utf-8,' + encodeURIComponent(window.editor.getValue()));
    element.setAttribute('download', "model.yaml");

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}

function uploadModel() {
    var fileToLoad = document.getElementById("file").files[0];

    var fileReader = new FileReader();
    fileReader.onload = function (fileLoadedEvent) {
        var textFromFileLoaded = fileLoadedEvent.target.result;
        window.editor.setValue(textFromFileLoaded);
    };

    fileReader.readAsText(fileToLoad, "UTF-8");
}

document.addEventListener("keydown", (event) => {
    if (event.key == 's' && (navigator.userAgentData.platform.match("Mac") ? event.metaKey : event.ctrlKey)) {
        event.preventDefault();
        downloadModel();
    }
}, false);