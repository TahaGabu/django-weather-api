(function () {
  const input = document.getElementById("city");
  if (!input) return;
  input.addEventListener("focus", function () {
    this.select();
  });
})();
