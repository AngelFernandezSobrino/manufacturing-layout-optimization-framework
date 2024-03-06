function request() {
    console.log("Send function request");



    postData("/run", window.editor.getValue()).then((data) => {
        console.log(); // JSON data parsed by `data.json()` call

        window.localStorage.setItem("result", JSON.stringify(data))

        document.querySelector("#result").classList.add("active")

        let resultsNode = document.querySelector("#result-content")
        let table = document.createElement("table")
        table.classList.add("plant-grid")
        resultsNode.appendChild(table)

        let thead = document.createElement("thead")
        table.appendChild(thead)
        let tr = document.createElement("tr")
        thead.appendChild(tr)
        let th = document.createElement("th")
        th.classList.add("index")
        tr.appendChild(th)
        data.forEach((column, column_index) => {
            let th = document.createElement("th")
            th.innerText = column_index + 1
            tr.appendChild(th)
        });

        let tbody = document.createElement("tbody")
        table.appendChild(tbody)
        data.forEach((row, row_index) => {
            let tr = document.createElement("tr")
            tbody.appendChild(tr)
            let th = document.createElement("th")
            th.innerText = row_index + 1
            th.classList.add("index")
            tr.appendChild(th)
            row.forEach((cell, column_index) => {
                let td = document.createElement("td")
                td.classList.add("plant-grid_station")
                if (cell != null) {
                    td.classList.add("plant-grid_active")
                }
                td.id = `plant-grid-${column_index}-${row_index}`
                cell != null ? td.innerHTML = `<p>${cell}</p>` : td.innerHTML = `<p> </p>`
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


function closeResult() {
    document.querySelector("#result").classList.remove("active")
    document.querySelector("#result-content").innerHTML = ""
}


function downloadResult() {
    var element = document.createElement('a');
    element.setAttribute('href', 'data:text/json;charset=utf-8,' + window.localStorage.getItem("result"));
    element.setAttribute('download', "results.json");

    element.style.display = 'none';
    document.body.appendChild(element);

    element.click();

    document.body.removeChild(element);
}