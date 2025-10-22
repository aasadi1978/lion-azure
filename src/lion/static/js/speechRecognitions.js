
// view-source:https://zolomohan.com/speech-recognition-in-javascript/
// https://zolomohan.com/speech-recognition-in-javascript/speechRecognition.js
// https://zolomohan.com/speech-recognition-in-javascript/language.js

if (!("webkitSpeechRecognition" in window)) {
    alert("Speech Recognition Not Available");
};

function speechRecognition_drivernote() {

    let speechRecognition = new webkitSpeechRecognition();
    let final_transcript = "";

    // Capture document title (browser tab)
    let document_title = document.title

    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'en-GB'

    speechRecognition.onstart = () => {
        changeBrowserTabTitle('Listenting ...')
    };
    speechRecognition.onerror = () => {
        changeBrowserTabTitle('Speech Recognition Error!')
    };
    speechRecognition.onend = () => {
        changeBrowserTabTitle(document_title)
    };

    speechRecognition.onresult = (event) => {
        let interim_transcript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                final_transcript += event.results[i][0].transcript;
            } else {
                interim_transcript += event.results[i][0].transcript;
            }
        }
        document.querySelector("#id-driver-note").innerHTML = final_transcript;
    };


    document.querySelector("#id-start-speech-driver-note").onclick = () => {
        speechRecognition.start();
    };

    document.querySelector("#id-stop-speech-driver-note").onclick = () => {
        speechRecognition.stop();
    };
    // speechRecognition = undefined
}

function speechRecognition_schedule_note() {

    let speechRecognition = new webkitSpeechRecognition();
    let final_transcript = "";

    // Capture document title (browser tab)
    let document_title = document.title

    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'en-GB'

    speechRecognition.onstart = () => {
        changeBrowserTabTitle('Listenting ...')
    };
    speechRecognition.onerror = () => {
        changeBrowserTabTitle('Speech Recognition Error!')
    };
    speechRecognition.onend = () => {
        changeBrowserTabTitle(document_title)
    };

    speechRecognition.onresult = (event) => {
        let interim_transcript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                final_transcript += event.results[i][0].transcript;
            } else {
                interim_transcript += event.results[i][0].transcript;
            }
        }
        document.querySelector("#id-scenario-note").innerHTML = final_transcript;
    };


    document.querySelector("#id-start-speech-schedule-note").onclick = () => {
        speechRecognition.start();
    };

    document.querySelector("#id-stop-speech-schedule-note").onclick = () => {
        speechRecognition.stop();
    };
    // speechRecognition = undefined
}

