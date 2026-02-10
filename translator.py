from dotenv import load_dotenv
import os

# Import namespaces
import azure.cognitiveservices.speech as speech_sdk



def main():
    try:
        global speech_config
        global translation_config

        # Get Configuration Settings (strip whitespace to avoid 401 auth errors)
        load_dotenv()
        ai_key = (os.getenv('SPEECH_KEY') or '').strip()
        ai_region = (os.getenv('SPEECH_REGION') or '').strip()
        ai_endpoint = (os.getenv('SPEECH_ENDPOINT') or '').strip()

        if not ai_key:
            raise ValueError('Missing SPEECH_KEY in .env.')
        if not ai_endpoint and not ai_region:
            raise ValueError(
                'Missing SPEECH_ENDPOINT or SPEECH_REGION in .env. '
                'Use SPEECH_ENDPOINT (e.g. https://eastus.api.cognitive.microsoft.com/) or SPEECH_REGION (e.g. eastus).'
            )

        # Configure translation (prefer endpoint URI when set)
        # Speech SDK requires WS/WSS scheme for endpoint, not HTTPS
        if ai_endpoint:
            speech_endpoint = ai_endpoint.replace('https://', 'wss://', 1).replace('http://', 'ws://', 1)
            translation_config = speech_sdk.translation.SpeechTranslationConfig(
                subscription=ai_key,
                endpoint=speech_endpoint
            )
            speech_config = speech_sdk.SpeechConfig(subscription=ai_key, endpoint=speech_endpoint)
        else:
            translation_config = speech_sdk.translation.SpeechTranslationConfig(
                subscription=ai_key,
                region=ai_region
            )
            speech_config = speech_sdk.SpeechConfig(subscription=ai_key, region=ai_region)

        translation_config.speech_recognition_language = 'en-US'
        translation_config.add_target_language('fr')
        translation_config.add_target_language('es')
        translation_config.add_target_language('hi')
        translation_config.add_target_language('kn')

        print('Ready to translate from', translation_config.speech_recognition_language)
        speech_config.speech_recognition_language = 'en-US'


        # Get user input
        targetLanguage = ''
        while targetLanguage != 'quit':
            targetLanguage = input('\nEnter a target language\n fr = French\n es = Spanish\n hi = Hindi\n kn = Kannada\n Enter anything else to stop\n').lower()
            if targetLanguage in translation_config.target_languages:
                Translate(targetLanguage)
            else:
                targetLanguage = 'quit'
                

    except Exception as ex:
        print(ex)

def Translate(targetLanguage):
    global translation_config, speech_config

    # Use default microphone for capture
    audio_config = speech_sdk.audio.AudioConfig(use_default_microphone=True)
    recognizer = speech_sdk.translation.TranslationRecognizer(
        translation_config=translation_config,
        audio_config=audio_config
    )

    print("Listening... Speak into your microphone (e.g. a short sentence in English).")
    result = recognizer.recognize_once()

    if result.reason == speech_sdk.ResultReason.TranslatedSpeech:
        recognized_text = result.text
        translation = result.translations.get(targetLanguage, "")
        print('Heard: "{}"'.format(recognized_text))
        print('Translation ({}): "{}"'.format(targetLanguage, translation))

        # Synthesize translation to speech
        if translation:
            voices = {
                "fr": "fr-FR-HenriNeural",
                "es": "es-ES-ElviraNeural",
                "hi": "hi-IN-MadhurNeural",
                "kn": "kn-IN-GaganNeural"
            }
            speech_config.speech_synthesis_voice_name = voices.get(targetLanguage)
            speech_synthesizer = speech_sdk.SpeechSynthesizer(speech_config=speech_config)
            speak = speech_synthesizer.speak_text_async(translation).get()
            if speak.reason != speech_sdk.ResultReason.SynthesizingAudioCompleted:
                print("Synthesis: {}".format(speak.reason))
    elif result.reason == speech_sdk.ResultReason.RecognizedSpeech:
        print('Heard: "{}" (no translation returned)'.format(result.text))
    elif result.reason == speech_sdk.ResultReason.NoMatch:
        print("No speech detected. Speak clearly and try again.")
        if result.no_match_details:
            print("  Details: {}".format(result.no_match_details))
    elif result.reason == speech_sdk.ResultReason.Canceled:
        print("Recognition canceled.")
        if result.cancellation_details.reason == speech_sdk.CancellationReason.Error:
            print("  Error: {}".format(result.cancellation_details.error_details))

if __name__ == "__main__":
    main()