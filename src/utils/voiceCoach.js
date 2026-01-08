let synth;
let recognition;

export async function initVoice(mode = "yoga") {
  synth = window.speechSynthesis;
  if ("webkitSpeechRecognition" in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.lang = "en-US";
  }
  console.log(`🦁 Voice initialized in ${mode} mode`);
}

export function speak(text) {
  if (!text || !window.speechSynthesis) return;
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.95;
  utter.pitch = 1.0;
  utter.volume = 1;
  utter.voice = speechSynthesis.getVoices().find((v) =>
    v.name.toLowerCase().includes("female")
  );
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
  console.log("🎙 Coach:", text);
}

export function listenForWakeWord(onWake) {
  if (!recognition) return;
  recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
    if (transcript.includes("hey coach")) {
      speak("I'm here — what do you need?");
      if (onWake) onWake();
    }
  };
  recognition.start();
  console.log("🎧 Listening for wake word: 'Hey Coach'");
}
