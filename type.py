import json
import os
import random
import time

# Fallback dictionary in case you haven't downloaded the full JSON file yet
SAMPLE_DICTIONARY = {
    "ephemeral": "Lasting for a very short time.",
    "serendipity": "Finding good things without looking for them.",
    "ubiquitous": "Present, appearing, or found everywhere.",
    "pragmatic": "Dealing with things sensibly and realistically.",
    "eloquent": "Fluent or persuasive in speaking or writing.",
    "resilient": "Able to recover quickly from difficult conditions.",
    "alacrity": "Brisk and cheerful readiness.",
    "lucid": "Expressed clearly; easy to understand.",
    "benevolent": "Well meaning and kindly.",
    "candid": "Truthful and straightforward; frank.",
}


def load_dictionary(filepath="dictionary.json"):
  """Loads a full JSON dictionary if available, otherwise uses the sample."""
  if os.path.exists(filepath):
    print(f"Loading full dictionary from {filepath}...")
    with open(filepath, "r", encoding="utf-8") as file:
      data = json.load(file)
      clean_dict = {}

      # Case 1: JSON is a standard dictionary {"word": "definition"}
      if isinstance(data, dict):
        for word, defn in data.items():
          if " " not in word and isinstance(defn, str):
            clean_dict[word.lower()] = defn

      # Case 2: JSON is a list of items
      elif isinstance(data, list):
        for item in data:
          # Subcase 2a: List of dicts, e.g. [{"word": "apple", "definition": "a fruit"}]
          if isinstance(item, dict):
            word = item.get("word") or item.get("term") or item.get("title")
            defn = (
                item.get("definition")
                or item.get("meaning")
                or item.get("definitions")
            )
            # If definitions are stored in a nested list, grab the first one
            if isinstance(defn, list) and len(defn) > 0:
              defn = str(defn[0])

            if (
                isinstance(word, str)
                and " " not in word
                and isinstance(defn, str)
            ):
              clean_dict[word.lower()] = defn

          # Subcase 2b: Simple list of words with no definitions, e.g. ["apple", "banana"]
          elif isinstance(item, str) and " " not in item:
            clean_dict[item.lower()] = "No definition available."

      print(f"Loaded {len(clean_dict):,} words!\n")
      return clean_dict if clean_dict else SAMPLE_DICTIONARY
  else:
    print("Full 'dictionary.json' not found. Running with built-in sample list.")
    print(
        "Tip: Place a 'dictionary.json' file in this folder for 100,000+"
        " words!\n"
    )
    return SAMPLE_DICTIONARY


def run_typing_test(dictionary, num_words=5):
  words_pool = list(dictionary.keys())
  selected_words = random.sample(words_pool, min(num_words, len(words_pool)))

  correct_count = 0
  total_chars_typed = 0

  print("--- TYPING SPEED & VOCABULARY TEST ---")
  input("Press ENTER when you are ready to start...")
  print("-" * 40)

  start_time = time.time()

  for i, word in enumerate(selected_words, 1):
    # Shorten very long definitions so the screen stays clean
    meaning = dictionary[word]
    if len(meaning) > 120:
      meaning = meaning[:117] + "..."

    print(f"\nWord {i}/{len(selected_words)}:  {word.upper()}")
    print(f"Meaning:   {meaning}")

    typed = input("Type here: ").strip().lower()

    if typed == word:
      print("✓ Correct!")
      correct_count += 1
      # Standard WPM counts 5 characters (including space) as 1 word
      total_chars_typed += len(word) + 1
    else:
      print(f"✗ Missed! (Expected: {word})")

  end_time = time.time()
  elapsed_minutes = (end_time - start_time) / 60

  # Calculate WPM and Accuracy
  wpm = (total_chars_typed / 5) / elapsed_minutes if elapsed_minutes > 0 else 0
  accuracy = (correct_count / len(selected_words)) * 100

  print("\n" + "=" * 40)
  print("                 RESULTS")
  print("=" * 40)
  print(f"Time Taken : {end_time - start_time:.2f} seconds")
  print(f"Accuracy   : {accuracy:.1f}% ({correct_count}/{len(selected_words)})")
  print(f"Speed      : {wpm:.1f} WPM (Words Per Minute)")
  print("=" * 40)


if __name__ == "__main__":
  word_bank = load_dictionary("dictionary.json")
  while True:
    try:
      count = int(input("\nHow many words would you like to practice? "))
      if count <= 0:
        print("Please enter a number greater than 0.")
        continue
      run_typing_test(word_bank, count)
    except ValueError:
      print("Please enter a valid number.")

    again = input("\nPlay again? (y/n): ").strip().lower()
    if again != "y":
      print("Great practice! Goodbye.")
      break
