📊 MCP Server Pattern Storage Specifications
json{
  "mcp_server_patterns": {
    "essential_patterns_to_store": {
      
      "behavioral_patterns": {
        "description": "Observable repeated actions and responses",
        "examples": [
          "Procrastination before difficult tasks",
          "Energy dips at specific times",
          "Social withdrawal when stressed",
          "Overcommitment patterns",
          "Decision paralysis triggers"
        ],
        "storage_requirements": [
          "Frequency metrics",
          "Temporal markers",
          "Environmental contexts",
          "Preceding triggers",
          "Resulting outcomes"
        ]
      },
      
      "cognitive_patterns": {
        "description": "Thinking patterns and mental models",
        "examples": [
          "All-or-nothing thinking",
          "Catastrophizing future scenarios",
          "Impostor syndrome triggers",
          "Perfectionism blockers",
          "Analysis paralysis conditions"
        ],
        "storage_requirements": [
          "Thought sequence documentation",
          "Belief statements",
          "Cognitive distortion types",
          "Counter-evidence collected",
          "Reframe success rates"
        ]
      },
      
      "emotional_patterns": {
        "description": "Recurring emotional responses",
        "examples": [
          "Anxiety before presentations",
          "Frustration with interruptions",
          "Joy from specific achievements",
          "Guilt patterns around rest",
          "Anger triggers and recovery"
        ],
        "storage_requirements": [
          "Emotion intensity (1-10)",
          "Duration metrics",
          "Physical sensations",
          "Trigger classifications",
          "Regulation strategies tried"
        ]
      },
      
      "systemic_patterns": {
        "description": "Cross-domain cascading effects",
        "examples": [
          "Poor sleep → low energy → poor decisions → stress → poor sleep",
          "Success → overconfidence → overcommitment → burnout → withdrawal",
          "Exercise → mood boost → productivity → confidence → social engagement"
        ],
        "storage_requirements": [
          "Causal chain mapping",
          "Domain interconnections",
          "Time delays between causes and effects",
          "Amplification factors",
          "Breaking point interventions"
        ]
      },
      
      "temporal_patterns": {
        "description": "Time-based recurring patterns",
        "examples": [
          "Monday motivation, Friday fatigue",
          "Seasonal mood variations",
          "Monthly energy cycles",
          "Time-of-day productivity peaks",
          "Weekend recovery patterns"
        ],
        "storage_requirements": [
          "Timestamp data",
          "Cyclical period identification",
          "Amplitude measurements",
          "Phase shift observations",
          "Environmental correlations"
        ]
      }
    },
    
    "pattern_metadata": {
      "confidence_tracking": {
        "initial_hypothesis": 0.3,
        "single_observation": 0.5,
        "repeated_observation": 0.7,
        "validated_experiment": 0.9,
        "long_term_stable": 0.95
      },
      
      "evolution_tracking": [
        "Discovery date and context",
        "Confirmation instances",
        "Contradiction instances",
        "Modification history",
        "Related pattern emergence"
      ],
      
      "impact_metrics": {
        "domains_affected": ["count", "list"],
        "intervention_attempts": "count",
        "successful_disruptions": "count",
        "time_to_resolution": "days",
        "recurrence_after_intervention": "boolean"
      }
    },
    
    "cross_reference_requirements": {
      "pattern_relationships": [
        "Causal (A causes B)",
        "Correlational (A occurs with B)",
        "Inhibitory (A prevents B)",
        "Amplifying (A strengthens B)",
        "Compensatory (A balances B)"
      ],
      
      "experiment_linkages": {
        "targeting_pattern": "pattern_id",
        "patterns_discovered": ["pattern_ids"],
        "patterns_disrupted": ["pattern_ids"],
        "patterns_strengthened": ["pattern_ids"]
      }
    }
  }
}