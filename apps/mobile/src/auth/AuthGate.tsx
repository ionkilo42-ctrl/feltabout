import { useRouter } from "expo-router";
import type React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { GradientButton } from "../components/GradientButton";
import { useAuth } from "./AuthContext";
import { colors, radii, shadow } from "../styles/theme";

type AuthGateProps = {
  children: React.ReactNode;
  message?: string;
};

export function AuthGate({
  children,
  message = "Sign in to save and review your Feltabout reflections.",
}: AuthGateProps) {
  const router = useRouter();
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.card}>
          <ActivityIndicator color={colors.text} />
          <Text style={styles.title}>Checking your session</Text>
          <Text style={styles.text}>Opening your Feltabout account.</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.card}>
          <Text style={styles.title}>Sign in to continue</Text>
          <Text style={styles.text}>{message}</Text>
          <GradientButton label="Sign in" onPress={() => router.push("/auth")} />
        </View>
      </SafeAreaView>
    );
  }

  return <>{children}</>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: 24 },
  card: {
    marginTop: 80,
    padding: 22,
    alignItems: "center",
    backgroundColor: colors.surfaceSoft,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
    ...shadow.card,
  },
  title: { fontSize: 18, fontWeight: "700", color: colors.text, marginTop: 12, marginBottom: 8 },
  text: { fontSize: 14, color: colors.textMuted, lineHeight: 21, textAlign: "center", marginBottom: 18 },
});
