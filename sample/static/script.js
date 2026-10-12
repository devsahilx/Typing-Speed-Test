function saveData() {
    fetch("/api/save_result", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: "tushar",
            wpm: 40,
            accuracy: 90,
            correct_chars: 200,
            wrong_chars: 10,
            seconds: 30
        })
    })
    .then(response => response.json())
    .then(data => {
        alert("Saved Successfully!");
        console.log(data);
    });
}