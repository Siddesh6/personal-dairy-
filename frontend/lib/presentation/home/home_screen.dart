import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          'L I F E M O V I E',
          style: textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            letterSpacing: 2.0,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.lock_outline, color: AppTheme.roseGold),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Streak Header
            _buildStreakCard(context),
            const SizedBox(height: 24.0),

            // Daily Prompt
            Text('TODAY\'S PROMPT', style: textTheme.labelMedium),
            const SizedBox(height: 8.0),
            _buildPromptCard(context),
            const SizedBox(height: 24.0),

            // Continue Editing
            Text('CONTINUE EDITING', style: textTheme.labelMedium),
            const SizedBox(height: 12.0),
            _buildHorizontalList(),
            const SizedBox(height: 24.0),

            // Recent Movies
            Text('RECENT MOVIES', style: textTheme.labelMedium),
            const SizedBox(height: 12.0),
            _buildMovieGrid(),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: AppTheme.baseObsidian,
        selectedItemColor: AppTheme.celestialViolet,
        unselectedItemColor: Colors.white30,
        currentIndex: 0,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.add_circle_outline), label: 'Create'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_today), label: 'Timeline'),
          BottomNavigationBarItem(icon: Icon(Icons.face), label: 'Studio'),
        ],
      ),
    );
  }

  Widget _buildStreakCard(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: const Color(0xFF14141A),
        borderRadius: BorderRadius.circular(16.0),
        border: Border.all(color: Colors.white12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Text('🔥', style: TextStyle(fontSize: 24.0)),
              const SizedBox(width: 8.0),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'STREAK: 12 DAYS',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: AppTheme.roseGold,
                        ),
                  ),
                  const Text(
                    'Keep capturing memories daily!',
                    style: TextStyle(color: Colors.white54, fontSize: 12.0),
                  ),
                ],
              ),
            ],
          ),
          const Icon(Icons.check_circle_outline, color: AppTheme.emeraldGreen),
        ],
      ),
    );
  }

  Widget _buildPromptCard(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.celestialViolet, Color(0xFF5A1FB8)],
        ),
        borderRadius: BorderRadius.circular(16.0),
        boxShadow: [
          BoxShadow(
            color: AppTheme.celestialViolet.withOpacity(0.3),
            blurRadius: 15.0,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'What made you smile today?',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12.0),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: AppTheme.celestialViolet,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8.0),
              ),
            ),
            onPressed: () {},
            child: const Text('Record Memory'),
          ),
        ],
      ),
    );
  }

  Widget _buildHorizontalList() {
    return SizedBox(
      height: 120.0,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: 2,
        separatorBuilder: (_, __) => const SizedBox(width: 12.0),
        itemBuilder: (context, index) {
          return Container(
            width: 200.0,
            padding: const EdgeInsets.all(12.0),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.04),
              borderRadius: BorderRadius.circular(12.0),
              border: Border.all(color: Colors.white12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  index == 0 ? 'Trip to Alps' : 'Leo\'s First Step',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  index == 0 ? 'Storyboard ready' : 'Stitching scene...',
                  style: const TextStyle(color: AppTheme.oceanTeal, fontSize: 12.0),
                ),
                LinearProgressIndicator(
                  value: index == 0 ? 0.75 : 0.40,
                  color: AppTheme.roseGold,
                  backgroundColor: Colors.white12,
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildMovieGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: 2,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12.0,
        mainAxisSpacing: 12.0,
        childAspectRatio: 1.2,
      ),
      itemBuilder: (context, index) {
        return Container(
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.04),
            borderRadius: BorderRadius.circular(12.0),
            border: Border.all(color: Colors.white12),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              const Icon(Icons.play_circle_outline, size: 36.0, color: Colors.white70),
              Positioned(
                bottom: 8.0,
                left: 8.0,
                child: Text(
                  index == 0 ? 'Summer picnic' : 'Rainy morning',
                  style: const TextStyle(fontSize: 12.0, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
