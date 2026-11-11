import type { Passage } from "./types";

export const SAMPLE_PASSAGES: Passage[] = [
  {
    id: "sample_01",
    title: "Photosynthesis",
    text:
      "Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy, usually from the sun, into chemical energy stored in glucose. This process occurs primarily in the chloroplasts of plant cells, using chlorophyll to absorb light. The overall equation is: 6CO2 + 6H2O + light energy -> C6H12O6 + 6O2. Photosynthesis is fundamental to life on Earth because it produces oxygen and forms the base of the food chain.",
  },
  {
    id: "sample_02",
    title: "Newton's Laws of Motion",
    text:
      "Newton's three laws of motion describe the relationship between a body and the forces acting upon it. The First Law states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force (inertia). The Second Law states that Force equals mass times acceleration (F = ma). The Third Law states that for every action there is an equal and opposite reaction. These laws form the foundation of classical mechanics.",
  },
  {
    id: "sample_03",
    title: "The Water Cycle",
    text:
      "The water cycle, also known as the hydrological cycle, describes the continuous movement of water on, above, and below the surface of the Earth. Key stages include evaporation (water turns to vapor from oceans and lakes), condensation (vapor cools to form clouds), precipitation (water falls as rain or snow), and collection (water gathers in rivers, lakes, and groundwater). The water cycle is driven by solar energy and gravity, and it is essential for distributing freshwater around the planet.",
  },
  {
    id: "sample_04",
    title: "DNA and Genetics",
    text:
      "Deoxyribonucleic acid (DNA) is a molecule that carries the genetic instructions for the development, functioning, growth, and reproduction of all known living organisms. DNA is structured as a double helix: two strands coiled around each other, made up of nucleotide base pairs. Adenine (A) pairs with thymine (T), and cytosine (C) pairs with guanine (G). Genes are specific sequences of DNA that encode instructions for building proteins, which carry out most of the work in cells.",
  },
  {
    id: "sample_05",
    title: "Supply and Demand in Economics",
    text:
      "Supply and demand is one of the most fundamental concepts in economics. Demand refers to how much of a product consumers are willing and able to buy at various prices, while supply refers to how much producers are willing and able to sell at various prices. When demand rises and supply remains constant, prices tend to increase. When supply exceeds demand, prices tend to fall. The equilibrium price is the point where quantity supplied equals quantity demanded, resulting in a stable market price.",
  },
];

export const HOME_EXAMPLES = [
  {
    key: "simplify",
    title: "Simplify notes",
    description: "Turn difficult notes into clear explanations.",
    text: SAMPLE_PASSAGES[0]!.text,
  },
  {
    key: "explain",
    title: "Explain a topic",
    description: "Learn a topic with a simple example.",
    text: "Explain gravity to a beginner and give an everyday example.",
  },
  {
    key: "quiz",
    title: "Generate a quiz",
    description: "Try a quiz based on sample study notes.",
    text: SAMPLE_PASSAGES[2]!.text,
  },
  {
    key: "revision",
    title: "Revision notes",
    description: "Make exam-ready notes from a sample topic.",
    text:
      "Cells are the basic units of life. The cell theory states that all living things are made of cells, cells are the basic unit of structure and function, and new cells come from existing cells.",
  },
] as const;
