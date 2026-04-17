window.isMobile = () => window.innerWidth <= 600;

window.mobileLayout = (layout) => {
  if (!window.isMobile()) return layout;
  const m = layout.margin || {};
  return {
    ...layout,
    font: { ...layout.font, size: 9 },
    margin: { t: m.t ?? 20, r: 8, b: Math.min(m.b ?? 40, 40), l: Math.min(m.l ?? 40, 36) },
  };
};

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const links  = document.querySelector('.nav-links');
  if (!toggle || !links) return;

  toggle.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    toggle.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', open);
  });

  links.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      links.classList.remove('open');
      toggle.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    });
  });
});
