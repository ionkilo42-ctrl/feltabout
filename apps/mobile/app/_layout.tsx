import { Stack } from "expo-router";
import { colors } from "../src/styles/theme";

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.text,
        headerTitleStyle: { fontWeight: "600" },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen
        name="reflection/new"
        options={{ title: "New Reflection", headerBackTitle: "Back" }}
      />
      <Stack.Screen
        name="reflection/[id]"
        options={{ title: "Reflection", headerBackTitle: "Back" }}
      />
      <Stack.Screen
        name="reflection/review"
        options={{ title: "Review", headerBackTitle: "Back" }}
      />
      <Stack.Screen
        name="reflection/plan"
        options={{ title: "Conversation Plan", headerBackTitle: "Back" }}
      />
    </Stack>
  );
}
