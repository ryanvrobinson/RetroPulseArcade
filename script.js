document.addEventListener("DOMContentLoaded", () => {
  fetch("tournament.json")
    .then(res => res.json())
    .then(data => {
      if (data) {
        if (data.player_name) {
          document.getElementById("player-nickname").textContent = data.player_name;
        }

        const keys = [
          "flash", "dodge", "spot_it", "archery", "traffic",
          "memory", "block_drop", "sky_dash", "find_secret", "color_chaos"
        ];

        if (data.player_scores) {
          keys.forEach(k => {
            const el = document.getElementById(`score-${k}`);
            if (el && data.player_scores[k] !== undefined) {
              el.textContent = data.player_scores[k];
            }
          });
        }
      }
    })
    .catch(() => {});

  const cards = document.querySelectorAll(".card");
  cards.forEach(card => {
    card.addEventListener("click", () => {
      card.style.transform = "scale(0.96)";
      setTimeout(() => {
        card.style.transform = "";
      }, 100);
    });
  });
});