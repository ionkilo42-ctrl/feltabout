import { LinearGradient } from "expo-linear-gradient";
import { Text, TouchableOpacity, StyleSheet, ViewStyle } from "react-native";
import { colors, gradient, radii } from "../styles/theme";

interface GradientButtonProps {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  style?: ViewStyle;
}

export function GradientButton({ label, onPress, disabled, style }: GradientButtonProps) {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.86}
      disabled={disabled}
      style={[styles.wrap, disabled && styles.disabled, style]}
    >
      <LinearGradient colors={gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.fill}>
        <Text style={styles.text}>{label}</Text>
      </LinearGradient>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderRadius: radii.pill,
    overflow: "hidden",
  },
  fill: {
    minHeight: 54,
    paddingHorizontal: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  text: {
    color: colors.surface,
    fontSize: 16,
    fontWeight: "700",
  },
  disabled: {
    opacity: 0.55,
  },
});
