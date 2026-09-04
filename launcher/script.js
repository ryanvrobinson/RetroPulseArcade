document.addEventListener("DOMContentLoaded", () => {
  fetch("highscores.json")
    .then(res => res.json())
    .then(data => {
      if (data) {
        const games = ["flash", "dodge", "spot_it", "archery", "traffic", "memory"];
        games.forEach(key => {
          const el = document.getElementById(`score-${key}`);
          if (el && data[key] !== undefined) {
            el.textContent = data[key];
          }
        });
      }
    })
    .catch(() => {
      // Graceful offline fallback
    });

  const cards = document.querySelectorAll(".card");
  cards.forEach(card => {
    card.addEventListener("click", () => {
      card.style.transform = "scale(0.96)";
      setTimeout(() => {
        card.style.transform = "";
      }, 120);
    });
  });
});