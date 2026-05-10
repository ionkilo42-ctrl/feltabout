import { useRouter } from "expo-router";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GradientButton } from "../src/components/GradientButton";
import { BrandMark } from "../src/components/BrandMark";
import { colors, radii, shadow } from "../src/styles/theme";

export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <BrandMark size={86} />
        <Text style={styles.logo}>feltabout</Text>
        <Text style={styles.tagline}>Reflect before you react.</Text>

        <View style={styles.description}>
          <Text style={styles.descriptionText}>
            Take a few minutes to understand what you're feeling, what you need,
            and how to approach a difficult conversation with clarity.
          </Text>
        </View>

        <GradientButton label="Start a reflection" onPress={() => router.push("/reflection/new")} />
        <TouchableOpacity style={styles.linkButton} onPress={() => router.push("/(tabs)/reflections")}>
          <Text style={styles.linkText}>Open reflection library</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Not therapy. Not a crisis line. Just a calm space to prepare.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: 32,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  logo: {
    fontSize: 42,
    fontWeight: "700",
    color: colors.text,
    letterSpacing: 0,
    marginBottom: 8,
    marginTop: 18,
  },
  tagline: {
    fontSize: 20,
    color: colors.textSoft,
    fontWeight: "500",
    marginBottom: 28,
  },
  description: {
    marginBottom: 34,
    padding: 22,
    borderRadius: radii.card,
    backgroundColor: colors.surfaceSoft,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
    ...shadow.card,
  },
  descriptionText: {
    fontSize: 16,
    color: colors.textMuted,
    textAlign: "center",
    lineHeight: 25,
  },
  linkButton: { marginTop: 16, paddingVertical: 10 },
  linkText: { color: colors.textMuted, fontSize: 15, fontWeight: "600" },
  footer: {
    paddingBottom: 32,
    alignItems: "center",
  },
  footerText: {
    fontSize: 13,
    color: colors.textQuiet,
    textAlign: "center",
  },
});
