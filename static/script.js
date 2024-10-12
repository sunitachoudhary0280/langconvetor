<script>
    $(document).ready(function () {
        $("#translate-button").click(function () {
            const textToTranslate = $("#text-input").val();
            const targetLanguage = $("#language-select").val(); // Assuming you have a select input for languages

            fetch("/api/translate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: textToTranslate, target: targetLanguage })
            })
            .then(response => response.json())
            .then(data => {
                $("#translated-output").text(data.translatedText); // Display translated text
            })
            .catch(error => console.error("Error:", error));
        })
    });
</script>
