import { LinearGradient } from "expo-linear-gradient";
import { Text, StyleSheet, View } from "react-native";
import { colors, gradient } from "../styles/theme";

export function BrandMark({ size = 74 }: { size?: number }) {
  return (
    <LinearGradient
      colors={gradient}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.mark, { width: size, height: size, borderRadius: size / 2 }]}
    >
      <View style={[styles.inner, { borderRadius: size / 2 }]}>
        <Text style={[styles.symbol, { fontSize: size * 0.34 }]}>felt</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  mark: {
    padding: 3,
  },
  inner: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.9)",
  },
  symbol: {
    color: colors.text,
    fontWeight: "700",
    letterSpacing: 0,
  },
});
