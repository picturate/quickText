from quicktext.imports import *
from quicktext.utils.configuration import read_yaml, merge_dictb_to_dicta

"""
Code for the neural net based on a repo by AnubhavGupta3377
https://github.com/AnubhavGupta3377/Text-Classification-Models-Pytorch
"""


class Seq2SeqAttention(nn.Module):
    def __init__(self, num_class=2, config=None):
        super(Seq2SeqAttention, self).__init__()

        main_dir = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(main_dir, "config.yml")
        default_config = read_yaml(config_path)

        config = (
            merge_dictb_to_dicta(default_config, config)
            if config is not None
            else default_config
        )

        # Embedding Layer
        self.embeddings = nn.Embedding(config.vocab_size, config.embedding_dim)

        # Encoder RNN
        self.lstm = nn.LSTM(
            input_size=config.embedding_dim,
            hidden_size=config.hidden_dim,
            num_layers=config.n_layers,
            bidirectional=config.bidirectional,
        )

        # Dropout Layer
        self.dropout = nn.Dropout(config.dropout)

        # Fully-Connected Layer
        self.fc = nn.Linear(
            config.hidden_dim * (1 + config.bidirectional) * 2, num_class
        )

        # Softmax non-linearity
        self.softmax = nn.Softmax()

        self.config = config

    def apply_attention(self, rnn_output, final_hidden_state):
        """
        Apply Attention on RNN output
        
        Input:
            rnn_output (batch_size, seq_len, num_directions * hidden_size): tensor representing hidden state for every word in the sentence
            final_hidden_state (batch_size, num_directions * hidden_size): final hidden state of the RNN
            
        Returns:
            attention_output(batch_size, num_directions * hidden_size): attention output vector for the batch
        """
        hidden_state = final_hidden_state.unsqueeze(2)
        attention_scores = torch.bmm(rnn_output, hidden_state).squeeze(2)
        soft_attention_weights = F.softmax(attention_scores, 1).unsqueeze(
            2
        )  # shape = (batch_size, seq_len, 1)
        attention_output = torch.bmm(
            rnn_output.permute(0, 2, 1), soft_attention_weights
        ).squeeze(2)
        return attention_output

    def forward(self, x, text_length):
        # x.shape = (max_sen_len, batch_size)
        x = x.permute(1, 0)

        embedded_sent = self.embeddings(x)
        # embedded_sent.shape = (max_sen_len=20, batch_size=64,embed_size=300)

        ##################################### Encoder #######################################
        lstm_output, (h_n, c_n) = self.lstm(embedded_sent)
        # lstm_output.shape = (seq_len, batch_size, num_directions * hidden_size)

        # Final hidden state of last layer (num_directions, batch_size, hidden_size)
        batch_size = h_n.shape[1]
        h_n_final_layer = h_n.view(
            self.config.hidden_dim,
            self.config.bidirectional + 1,
            batch_size,
            self.config.hidden_dim,
        )[-1, :, :, :]

        ##################################### Attention #####################################
        # Convert input to (batch_size, num_directions * hidden_size) for attention
        final_hidden_state = torch.cat(
            [h_n_final_layer[i, :, :] for i in range(h_n_final_layer.shape[0])], dim=1
        )

        attention_out = self.apply_attention(
            lstm_output.permute(1, 0, 2), final_hidden_state
        )
        # Attention_out.shape = (batch_size, num_directions * hidden_size)

        #################################### Linear #########################################
        concatenated_vector = torch.cat([final_hidden_state, attention_out], dim=1)
        final_feature_map = self.dropout(
            concatenated_vector
        )  # shape=(batch_size, num_directions * hidden_size)

        final_out = self.fc(final_feature_map)
        return final_out
