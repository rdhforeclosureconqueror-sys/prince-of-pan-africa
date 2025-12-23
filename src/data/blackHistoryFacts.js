// src/data/blackHistoryFacts.js

export const BLACK_HISTORY_MONTHLY = {
  January: [
    "1970: The first issue of The Black Scholar was published (early 1970).",
    "1986: Dr. Martin Luther King Jr. Day began being observed as a U.S. federal holiday (first observed in 1986).",
    "1863: The Emancipation Proclamation took effect on Jan 1, 1863.",
  ],
  February: [
    "1926: Carter G. Woodson launched Negro History Week (the seed of Black History Month).",
    "1965: Malcolm X was assassinated (Feb 21, 1965).",
    "1960: Greensboro sit-ins began (Feb 1, 1960).",
  ],
  March: [
    "1965: Selma to Montgomery marches took place (March 1965).",
    "1870: The 15th Amendment was ratified (Feb 1870) — often taught alongside spring civics units.",
    "1995: Million Man March planning and organizing gained momentum in early 1995 (contextual).",
  ],
  April: [
    "1968: Dr. Martin Luther King Jr. was assassinated (Apr 4, 1968).",
    "1968: The Fair Housing Act was signed (Apr 11, 1968).",
    "1947: Jackie Robinson broke MLB’s color line (Apr 15, 1947).",
  ],
  May: [
    "1954: Brown v. Board of Education decision (May 17, 1954).",
    "1961: Freedom Rides began (May 1961).",
    "1972: Shirley Chisholm ran for president and won multiple primaries (spring 1972).",
  ],
  June: [
    "1865: Juneteenth commemorates emancipation news reaching Texas (June 19, 1865).",
    "1967: Loving v. Virginia decision (June 12, 1967).",
    "1971: The Congressional Black Caucus was founded (1971).",
  ],
  July: [
    "1852: Frederick Douglass delivered 'What to the Slave is the Fourth of July?' (July 1852).",
    "1967: Major urban uprisings occurred in summer 1967 (Detroit/Newark context).",
    "1995: Nelson Mandela visited the U.S. often referenced in summer international highlights (contextual).",
  ],
  August: [
    "1963: March on Washington (Aug 28, 1963).",
    "1791: Haitian Revolution began (Aug 1791).",
    "1619: First documented arrival of enslaved Africans to English North America (Aug 1619).",
  ],
  September: [
    "1957: Little Rock Nine integrated Central High (Sept 1957).",
    "1962: James Meredith integrated the University of Mississippi (Sept 1962).",
    "1973: Hip-hop culture’s birth is often traced to Aug 1973; early fall celebrates its spread (contextual).",
  ],
  October: [
    "1968: Tommie Smith & John Carlos Olympic protest (Oct 1968).",
    "1995: Million Man March (Oct 16, 1995).",
    "1901: Booker T. Washington dined at the White House (Oct 1901).",
  ],
  November: [
    "1960: Ruby Bridges integrated a New Orleans school (Nov 14, 1960).",
    "1872: P.B.S. Pinchback became acting governor of Louisiana (late 1872 context).",
    "2008: Barack Obama elected president (Nov 4, 2008).",
  ],
  December: [
    "1865: The 13th Amendment was ratified (Dec 6, 1865).",
    "1955: Montgomery Bus Boycott began (Dec 5, 1955).",
    "1993: Nelson Mandela and F.W. de Klerk received the Nobel Peace Prize (Dec 1993).",
  ],
};

export function getMonthlyHighlights(monthName) {
  return BLACK_HISTORY_MONTHLY[monthName] || [];
}
