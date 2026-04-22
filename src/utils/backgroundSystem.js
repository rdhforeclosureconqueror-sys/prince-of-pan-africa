const BACKGROUND_ASSETS = [
  "/images/backgroundunity.png",
  "/images/background1.png",
  "/images/background2.png",
  "/images/backgrounddogon.png",
  "/images/backgroundbenin.png",
  "/images/egypt_backgrond3.png",
];

const BACKGROUND_POOLS = {
  home: ["/images/backgroundunity.png", "/images/background1.png", "/images/background2.png"],
  languages: ["/images/backgroundbenin.png", "/images/backgrounddogon.png", "/images/backgroundunity.png"],
  library: ["/images/egypt_backgrond3.png", "/images/backgrounddogon.png", "/images/background2.png"],
  leadership: ["/images/background1.png", "/images/backgroundunity.png", "/images/backgroundbenin.png"],
  operations: ["/images/background2.png", "/images/egypt_backgrond3.png", "/images/backgroundunity.png"],
  default: BACKGROUND_ASSETS,
};

const GROUP_ROUTES = [
  { key: "home", match: (path) => path === "/" },
  { key: "languages", match: (path) => path.startsWith("/languages") || path.startsWith("/language") },
  { key: "library", match: (path) => path.startsWith("/library") || path.startsWith("/study") || path.startsWith("/decolonize") || path.startsWith("/portal/decolonize") },
  { key: "leadership", match: (path) => path.startsWith("/leadership") || path.startsWith("/results") },
  { key: "operations", match: (path) => path.startsWith("/dashboard") || path.startsWith("/ops") },
];

const ROTATION_KEY = "ppa:bg:rotation-index";
const SESSION_KEY = "ppa:bg:session-seeded";

function hashString(input) {
  let h = 0;
  for (let i = 0; i < input.length; i += 1) {
    h = (h << 5) - h + input.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

function seedForSession() {
  if (typeof window === "undefined") return 0;

  const seededThisSession = sessionStorage.getItem(SESSION_KEY);
  if (!seededThisSession) {
    const current = Number(localStorage.getItem(ROTATION_KEY) || 0);
    localStorage.setItem(ROTATION_KEY, String(current + 1));
    sessionStorage.setItem(SESSION_KEY, "1");
    return current + 1;
  }

  return Number(localStorage.getItem(ROTATION_KEY) || 0);
}

function groupForPath(pathname) {
  const found = GROUP_ROUTES.find((route) => route.match(pathname));
  return found?.key || "default";
}

export function getBackgroundForPath(pathname) {
  const group = groupForPath(pathname);
  const pool = BACKGROUND_POOLS[group] || BACKGROUND_POOLS.default;
  const sessionSeed = seedForSession();
  const index = (sessionSeed + hashString(group)) % pool.length;

  return {
    group,
    image: pool[index],
  };
}

export function getLanguageBackgroundByName(languageName = "") {
  const key = languageName.toLowerCase();
  if (key.includes("swahili")) return "/images/backgroundbenin.png";
  if (key.includes("yoruba")) return "/images/backgrounddogon.png";
  return "/images/backgroundunity.png";
}
