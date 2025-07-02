import 'package:supabase_flutter/supabase_flutter.dart';

class SupabaseConfig {
  static const String supabaseUrl = 'https://uvgxnkzsncdoztznkkeh.supabase.co';
  static const String supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2Z3hua3pzbmNkb3p0em5ra2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE0MDMyOTksImV4cCI6MjA2Njk3OTI5OX0.LtLQAbOagC0Ek1YllxW4vHCsVC3FR6szW9VRptmmtkI';
  
  static Future<void> initialize() async {
    await Supabase.initialize(
      url: supabaseUrl,
      anonKey: supabaseAnonKey,
    );
  }
  
  static SupabaseClient get client => Supabase.instance.client;
}