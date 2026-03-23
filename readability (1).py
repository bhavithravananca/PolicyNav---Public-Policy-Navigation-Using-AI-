import textstat

class ReadabilityAnalyzer:
    def __init__(self, text):
        self.text = text

    def get_all_metrics(self):
        metrics = {
            "Flesch Reading Ease": textstat.flesch_reading_ease(self.text),
            "Flesch-Kincaid Grade": textstat.flesch_kincaid_grade(self.text),
            "SMOG Index": textstat.smog_index(self.text),
            "Gunning Fog": textstat.gunning_fog(self.text),
            "Coleman-Liau": textstat.coleman_liau_index(self.text)
        }

        metrics["Overall Grade Level"] = (
            metrics["Flesch-Kincaid Grade"]
            + metrics["SMOG Index"]
            + metrics["Gunning Fog"]
            + metrics["Coleman-Liau"]
        ) / 4

        metrics["Total Sentences"] = textstat.sentence_count(self.text)
        metrics["Total Words"] = textstat.lexicon_count(self.text)
        metrics["Total Syllables"] = textstat.syllable_count(self.text)
        metrics["Complex Words"] = textstat.difficult_words(self.text)
        metrics["Total Characters"] = len(self.text)

        return metrics