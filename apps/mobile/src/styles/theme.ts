import { StyleSheet } from "react-native";

export const colors = {
  background: "#F7F5F2",
  surface: "#FFFFFF",
  surfaceSoft: "rgba(255,255,255,0.82)",
  text: "#1E1E1E",
  textSoft: "#4A4A4A",
  textMuted: "#666666",
  textQuiet: "#A3A3A3",
  border: "#E8E4DF",
  accent: "#33D6C8",
  coral: "#FF6B6B",
  amber: "#FFB547",
  success: "#5BA88D",
  warning: "#D4A055",
  error: "#D46B6B",
};

export const gradient = ["#00C2FF", "#33D6C8", "#FF6B6B", "#FFB547"] as const;

export const radii = {
  pill: 999,
  card: 28,
  panel: 22,
  control: 16,
};

export const shadow = StyleSheet.create({
  card: {
    shadowColor: "#1E1E1E",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 28,
    elevation: 3,
  },
});
