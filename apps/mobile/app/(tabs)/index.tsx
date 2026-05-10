import { useRouter } from "expo-router";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GradientButton } from "../../src/components/GradientButton";
import { BrandMark } from "../../src/components/BrandMark";
import { colors, radii, shadow } from "../../src/styles/theme";

export default function HomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <View style={styles.hero}>
        <BrandMark />
        <Text style={styles.heroLogo}>feltabout</Text>
        <Text style={styles.heroTagline}>Reflect before you react.</Text>
        <Text style={styles.heroCopy}>
          AI-guided reflection and conversation preparation for difficult moments.
        </Text>
      </View>

      <View style={styles.actions}>
        <GradientButton label="Start a new reflection" onPress={() => router.push("/reflection/new")} />

        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => router.push("/(tabs)/reflections")}
          activeOpacity={0.8}
        >
          <Text style={styles.secondaryButtonText}>View reflections</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.info}>
        <Text style={styles.infoEyebrow}>Individual MVP</Text>
        <Text style={styles.infoTitle}>Untangle emotion into a clearer next sentence.</Text>
        <Text style={styles.infoText}>
          One focused reflection flow helps you name what happened, what you feel,
          what you need, and how to open the conversation without escalating it.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: 24 },
  hero: { alignItems: "center", marginTop: 44, marginBottom: 36 },
  heroLogo: { fontSize: 46, fontWeight: "700", color: colors.text, letterSpacing: 0, marginTop: 18 },
  heroTagline: { fontSize: 20, color: colors.textSoft, marginTop: 6, fontWeight: "500" },
  heroCopy: { fontSize: 15, color: colors.textMuted, lineHeight: 24, textAlign: "center", marginTop: 18, maxWidth: 310 },
  actions: { gap: 12, marginBottom: 34 },
  secondaryButton: { backgroundColor: "transparent", paddingVertical: 17, borderRadius: radii.pill, alignItems: "center", borderWidth: 1, borderColor: colors.border },
  secondaryButtonText: { color: colors.text, fontSize: 16, fontWeight: "600" },
  info: { padding: 22, borderRadius: radii.card, backgroundColor: colors.surfaceSoft, borderWidth: 1, borderColor: "rgba(0,0,0,0.04)", ...shadow.card },
  infoEyebrow: { fontSize: 12, color: colors.textQuiet, fontWeight: "700", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 },
  infoTitle: { fontSize: 18, fontWeight: "700", color: colors.text, marginBottom: 10, lineHeight: 25 },
  infoText: { fontSize: 14, color: colors.textMuted, lineHeight: 22 },
});
