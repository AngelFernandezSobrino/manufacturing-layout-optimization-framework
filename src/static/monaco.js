require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor@latest/min/vs', 'monaco-yaml': 'https://cdn.jsdelivr.net/npm/monaco-yaml@5.1.1' }});
window.MonacoEnvironment = { getWorkerUrl: () => proxy };



let proxy = URL.createObjectURL(new Blob([`
	self.MonacoEnvironment = {
		baseUrl: 'https://unpkg.com/monaco-editor@latest/min/'
	};
	importScripts('https://unpkg.com/monaco-editor@latest/min/vs/base/worker/workerMain.js');
`], { type: 'text/javascript' }));

require(["vs/editor/editor.main"], function () {
	
	window.monado = monaco

	window.editor = monaco.editor.create(document.getElementById('container'), {
		automaticLayout: true,
		theme: 'vs-dark',
		languaje: "yaml"
	});
});