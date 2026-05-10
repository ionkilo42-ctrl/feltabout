import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { BrandMark } from "../src/components/BrandMark";
import { GradientButton } from "../src/components/GradientButton";
import { useAuth } from "../src/auth/AuthContext";
import { colors, radii, shadow } from "../src/styles/theme";

type AuthMode = "login" | "register";

export default function AuthScreen() {
  const router = useRouter();
  const { mode: initialMode } = useLocalSearchParams<{ mode?: string }>();
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<AuthMode>(initialMode === "register" ? "register" : "login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const isRegister = mode === "register";

  async function handleSubmit() {
    setError("");
    if (!email.trim() || !password) {
      setError("Enter your email and password.");
      return;
    }
    if (isRegister && password.length < 8) {
      setError("Use at least 8 characters for your password.");
      return;
    }

    setSubmitting(true);
    try {
      if (isRegister) {
        await signUp({
          email: email.trim(),
          password,
          display_name: name.trim() || email.trim().split("@")[0],
        });
      } else {
        await signIn({ email: email.trim(), password });
      }
      router.replace("/(tabs)");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not connect to Feltabout.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.keyboard}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.brand}>
            <BrandMark size={68} />
            <Text style={styles.logo}>feltabout</Text>
            <Text style={styles.tagline}>Reflect before you react.</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.title}>{isRegister ? "Create your account" : "Sign in"}</Text>
            <Text style={styles.copy}>
              Save reflections, prepare conversation plans, and keep your library tied to your account.
            </Text>

            {isRegister ? (
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={setName}
                placeholder="Your name"
                placeholderTextColor={colors.textQuiet}
                autoCapitalize="words"
                autoComplete="name"
              />
            ) : null}

            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="Email"
              placeholderTextColor={colors.textQuiet}
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
            />
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder={isRegister ? "Password (8+ characters)" : "Password"}
              placeholderTextColor={colors.textQuiet}
              autoCapitalize="none"
              autoComplete={isRegister ? "new-password" : "current-password"}
              secureTextEntry
            />

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <GradientButton
              label={submitting ? "Please wait..." : isRegister ? "Create account" : "Sign in"}
              onPress={handleSubmit}
              disabled={submitting}
            />

            {submitting ? <ActivityIndicator style={styles.spinner} color={colors.text} /> : null}

            <TouchableOpacity
              style={styles.switchButton}
              onPress={() => {
                setError("");
                setMode(isRegister ? "login" : "register");
              }}
            >
              <Text style={styles.switchText}>
                {isRegister ? "Already have an account? Sign in" : "New here? Create an account"}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.disclaimer}>
            Feltabout is for reflection and communication support. It is not therapy, medical care, or crisis support.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  keyboard: { flex: 1 },
  content: { flexGrow: 1, justifyContent: "center", padding: 24 },
  brand: { alignItems: "center", marginBottom: 24 },
  logo: { fontSize: 38, fontWeight: "700", color: colors.text, marginTop: 14 },
  tagline: { fontSize: 16, color: colors.textSoft, marginTop: 4 },
  card: {
    backgroundColor: colors.surfaceSoft,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: "rgba(0,0,0,0.04)",
    padding: 22,
    ...shadow.card,
  },
  title: { fontSize: 24, fontWeight: "700", color: colors.text, marginBottom: 8 },
  copy: { fontSize: 14, color: colors.textMuted, lineHeight: 21, marginBottom: 20 },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.control,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    marginBottom: 12,
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  error: { color: colors.error, fontSize: 14, lineHeight: 20, marginBottom: 14 },
  spinner: { marginTop: 14 },
  switchButton: { alignItems: "center", marginTop: 18, paddingVertical: 6 },
  switchText: { color: colors.textMuted, fontSize: 14, fontWeight: "600" },
  disclaimer: {
    color: colors.textQuiet,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 22,
    textAlign: "center",
  },
});
