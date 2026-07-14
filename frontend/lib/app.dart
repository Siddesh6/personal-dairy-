import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'presentation/home/home_screen.dart';

class LifeMovieApp extends StatelessWidget {
  const LifeMovieApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LifeMovie AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const HomeScreen(),
    );
  }
}
