import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Brand HSL Color mappings to Flutter Colors
  static const Color baseObsidian = Color(0xFF0B0B0F); // hsl(240, 20%, 6%)
  static const Color celestialViolet = Color(0xFF822FF2); // hsl(265, 80%, 60%)
  static const Color roseGold = Color(0xFFEB7BA5); // hsl(340, 75%, 70%)
  static const Color oceanTeal = Color(0xFF22BECB); // hsl(180, 70%, 45%)
  static const Color emeraldGreen = Color(0xFF1DBB6E); // hsl(145, 75%, 45%)
  static const Color crimsonRed = Color(0xFFEE2A43); // hsl(355, 80%, 55%)

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: baseObsidian,
      colorScheme: const ColorScheme.dark(
        primary: celestialViolet,
        secondary: roseGold,
        background: baseObsidian,
        error: crimsonRed,
        surface: Color(0xFF14141A),
      ),
      textTheme: TextTheme(
        displayLarge: GoogleFonts.outfit(
          fontSize: 32.0,
          fontWeight: FontWeight.bold,
          letterSpacing: -0.02,
          color: Colors.white,
        ),
        titleLarge: GoogleFonts.outfit(
          fontSize: 24.0,
          fontWeight: FontWeight.bold,
          letterSpacing: -0.01,
          color: Colors.white,
        ),
        titleMedium: GoogleFonts.outfit(
          fontSize: 18.0,
          fontWeight: FontWeight.w500,
          color: Colors.white,
        ),
        bodyLarge: GoogleFonts.inter(
          fontSize: 14.0,
          fontWeight: FontWeight.normal,
          letterSpacing: 0.01,
          color: Colors.white,
        ),
        labelMedium: GoogleFonts.inter(
          fontSize: 11.0,
          fontWeight: FontWeight.w500,
          letterSpacing: 0.02,
          color: Colors.white70,
        ),
      ),
    );
  }
}
