from transformers import TrainingArguments

def training_args(output_dir='noisy_filtering',
                       smoothing=0.0, 
                       lr=2e-5,
                       epochs = 3,
                       bs = 16): 

    training_arguments=TrainingArguments(
                    output_dir= "src/training/" + output_dir + '/models',
                    learning_rate=lr,
                    warmup_steps=500,
                    per_device_train_batch_size=bs,
                    per_device_eval_batch_size=bs,
                    num_train_epochs=epochs,
                    weight_decay=0.01,
                    evaluation_strategy="epoch",
                    save_strategy="epoch",
                    load_best_model_at_end=True,
                    logging_steps=100,
                    label_smoothing_factor=smoothing,
                    seed = 42
                    )
    return training_arguments
