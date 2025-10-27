## **Drum Classifier Module**

This module is responsible for preparing the drum dataset, training a robust multi-label drum classification model, and saving the necessary components for later inference. The goal is to accurately identify individual drum sounds and, importantly, **simultaneous drum hits** (e.g., a *kick* and *snare* played at the exact same moment) from audio.

<!--date_created:thurs10-jul2025-->
<!--date_updated:sat12-jul2025-->

---
### **Prerequisites**

 * `Python >=3.12` installed.
 *  All required Python packages. You can install them by navigating to your project*s root directory (`DrumScript/`) in your terminal and running:
    
    
    ```zsh
    pip install -r requirements.txt
    ```    
    > Ensure your `requirements.txt` is up-to-date with `tensorflow`, `librosa`, `pretty_midi`, `soundfile`, `pandas`, `numpy`, `scikit-learn`, `tqdm`).
  * The raw **[ENST](https://magenta.tensorflow.org/datasets/e-gmd)** dataset downloaded and placed in `training_data/ENST/`. Make sure it includes the `info.csv` file, and the audio/`MIDI` subdirectories.
>
---
## **Processing the **ENST** dataset**

### Why process the data?

The raw **[ENST](https://magenta.tensorflow.org/datasets/e-gmd)** dataset provides full audio tracks and corresponding `MIDI` files for drum performances. 

However, for **training a classification model**, we don*t want to **analyse entire songs**. 

**Instead, we need:**

* **Individual Events:** Short audio segments that each contain a single drum hit or a distinct simultaneous combination of drum hits.
* **Accurate Labeling:** Each segment needs to be labeled with *exactly* which drum (or drums) are present.

Traditional drum sheet music and real drumming often involve multiple drums hitting at the same precise moment (e.g., a drummer playing a *kick* and *snare* simultaneously). A simple single-label classifier (e.g., this is a *kick* OR this is a *snare*) cannot capture these compound events.

Therefore, our data processing script `process_enst_dataset.py` does the following:
* It reads the `MIDI` files to identify precise **onset times** (when a drum sound starts).
* For each unique onset time, it identifies *all* `MIDI` notes (and thus all drum types) that begin at that exact moment. This allows us to create **multi-label examples** (e.g., an audio segment might be labeled as both *kick* and *snare*).
* It extracts a small, fixed-length audio segment centered around each identified onset.
* It saves these individual audio segments into a new directory (`training_data/ENST_processed/`) and generates a `multi_label_events.csv` file, which maps each audio segment filename to its one-hot encoded multi-labels.

### How to run

From the `DrumScript/` project root directory, run the script:

```bash
python3 -m training_data.ENST.process_enst_dataset
```

> **Important Note for VS Code Users:**
> Generating over 300,000 small `.wav` files can significantly slow down VS Code (due to indexing and scanning). To fix this, after running the script:
>
>1.  Open VS Code Settings (`Ctrl + ,` or `Cmd + ,`).
>2.  Search for `files.exclude`. Click Add Pattern and enter `**/training_data/ENST_processed/**`.
>3.  Search for `search.exclude`. Click Add Pattern and enter `**/training_data/ENST_processed/**`.
>4.  Completely close and reopen VS Code. This will tell VS Code to ignore that large directory, restoring performance.

---
## **Model training**

### Why train a model?

After preparing the multi-label dataset, we need a machine learning model that can learn the acoustic characteristics of each drum type, including how they sound when played in combination. The model will analyse the features extracted from the audio segments and learn to predict the correct multi-label output.

We use a **Convolutional Neural Network (CNN)** for this task because:

  * **Feature Learning:** `CNN`'s are excellent at automatically learning hierarchical features from raw data, such as the spectro-temporal patterns in audio (like `MFCC`'s).
  * **Multi-Label Capability:** With a `sigmoid` activation function in its output layer and `BinaryCrossentropy` as its loss function, a `CNN` can naturally predict the probability of *each* drum type being present independently, making it ideal for multi-label classification. This is a significant improvement over simpler models like **Random Forest**s, which are not designed for this kind of output.

The `model_trainer.py` script will:

  * Load the processed audio segments and their multi-labels from `training_data/ENST_processed/`.
  * Extract `MFCC` features from each segment.
  * Normalise these features using a `StandardScaler`.
  * Split the data into training and testing sets.
  * Define, compile, and train the `CNN model`.
  * Evaluate the models performance using **multi-label metrics** (e.g., `Binary Accuracy`, `Precision`, `Recall`, `AUC`).
  * Save the trained `CNN` model (`.h5` format), the `StandardScaler` (`.joblib` format), and the `label_map` (`.json` format) into the `models/` directory for later use in the main application.

> `AUC` stands for **Area Under the Receiver Operating Characteristic (ROC) Curve**
> * **Receiver Operating Characteristic (ROC) Curve:** This is a graphical plot that illustrates the diagnostic ability of a binary classifier system as its discrimination > threshold is varied. It plots the True Positive Rate (Sensitivity) against the False Positive Rate (1 - Specificity) at various threshold settings.
> 
> * **Area Under the Curve (AUC):** The `AUC` represents the degree or measure of separability. It tells us how much the model is capable of distinguishing between classes.
>    * An `AUC` of 1.0 means the model is perfect at distinguishing between the positive and negative classes.
>    * An `AUC` of 0.5 means the model has no discriminative ability, performing no better than random guessing.
>    * An `AUC` between 0.5 and 1.0 indicates varying degrees of predictive power; the closer to 1.0, the better.
> 
>* **Relevance for Multi-Label Classification:** In a multi-label context, like your drum classifier where a single audio segment can have multiple drum sounds present simultaneously, `AUC` is typically calculated for each individual label (e.g., *kick*, *snare*, *hi-hat*) and then averaged to give an overall score. This is indicated by the `multi_label=True` parameter used in the `model_trainer.py` script*s metric definition, ensuring that the `AUC` is computed appropriately across all possible drum types. It provides a robust measure of the model*s ability to correctly identify the presence or absence of each drum sound, regardless of the classification threshold you might eventually choose.
>

### How to run



From the `DrumScript/` project root directory, run the script:

```python
python3 -m drum_classifier.model_trainer training_data
```

or 

```python
python3 drum_classifier/model_trainer.py >> drum_classifier/training_log.txt
```

You should see something like this in Terminal:

```bash
(DrumScript) % python3 drum_classifier/model_trainer.py >> drum_classifier/training_log.txt
Feature Extraction:  23%|██████████████████████████████████████████████████████▋                                                                                                                                                                                  | 71792/305780 [02:13<07:50, 497.17it/s]
```

Depending on your compute-capability, it will take **approximately 10 minutes** to train the model, as it involves processing over **300,000 audio segments** and **training a deep learning model**.



> **TIP:** 
> 
> It is **recommended** that you track the output of `model_trainer.py` runs in order to diagnose outcomes. The easiest way to do this is to append the command `>> drum_classifier/training_log.txt` to the end of the command below when you run it. 
> 
> This will either a) **create a new `.txt` file** in `./drum_classifier` module folder (or wherever you specify the path) called `training_data.txt`, b) **append the output to the existing file** (assuming you use the same path/file_name). 
>  Once the script completes the file will contain the results of the run. 
---

<!--END-->