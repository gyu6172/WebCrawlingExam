"""각 Step의 코드 스니펫을 다크 배경 이미지로 렌더링 (PDF 양식 모방)"""
import os
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager

# 한글이 포함된 코멘트도 렌더되도록 폴백 폰트 설정
matplotlib.rcParams['font.family'] = ['Consolas', 'Malgun Gothic']
matplotlib.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))

# 다크 테마 색상 (VSCode-ish)
BG = '#1e1e1e'
FG = '#d4d4d4'
KW = '#569cd6'      # keyword
STR = '#ce9178'     # string
NUM = '#b5cea8'     # number
COMMENT = '#6a9955' # comment
FUNC = '#dcdcaa'    # function name
TYPE = '#4ec9b0'    # class/type

def render(filename, lines, width_in=8.0, fontsize=11):
    """lines: list of (text, color) tuples per line, or list of list of (text,color) for multi-token lines"""
    h = 0.30 * len(lines) + 0.4
    fig, ax = plt.subplots(figsize=(width_in, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, len(lines)+0.5)
    ax.axis('off')
    for i, line in enumerate(lines):
        y = len(lines) - i - 0.3
        if isinstance(line, str):
            ax.text(0.015, y, line, color=FG, family='Consolas', fontsize=fontsize, va='center')
        else:
            x = 0.015
            for text, color in line:
                ax.text(x, y, text, color=color, family='Consolas', fontsize=fontsize, va='center')
                # approx width: monospace ~ 0.011 per char at fontsize 11
                x += len(text) * (fontsize * 0.0009)
    plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(OUT, filename), dpi=160, facecolor=BG, bbox_inches='tight')
    plt.close()

# Step 0
render("code_step0.png", [
    [("import", KW), (" torch", FG)],
    [("import", KW), (" torch.nn", FG), (" as", KW), (" nn", FG)],
    [("import", KW), (" torch.optim", FG), (" as", KW), (" optim", FG)],
    [("import", KW), (" matplotlib.pyplot", FG), (" as", KW), (" plt", FG)],
    [("import", KW), (" numpy", FG), (" as", KW), (" np", FG)],
])

# Step 1
render("code_step1.png", [
    [("corpus", FG), (" = [", FG)],
    [('    "he is a king",', STR)],
    [('    "she is a queen",', STR)],
    [('    "he is a man", "she is a woman",', STR)],
    [('    "seoul is korea capital",', STR)],
    [('    "tokyo is japan capital",', STR)],
    [('    "paris is france capital"', STR)],
    [("]", FG)],
    [("words", FG), (" = ", FG), ('" "', STR), (".join(corpus).split()", FG)],
    [("word_list", FG), (" = ", FG), ("list", FUNC), ("(", FG), ("set", FUNC), ("(words))", FG)],
    [("word_dict", FG), (" = {w: i ", FG), ("for", KW), (" i, w ", FG), ("in", KW), (" enumerate(word_list)}", FG)],
    [("vocab_size", FG), (" = ", FG), ("len", FUNC), ("(word_dict)", FG)],
])

# Step 2
render("code_step2.png", [
    [("window_size", FG), (" = ", FG), ("1", NUM)],
    [("skip_grams", FG), (" = []", FG)],
    [("for", KW), (" sentence ", FG), ("in", KW), (" corpus:", FG)],
    [("    tokens = sentence.split()", FG)],
    [("    ", FG), ("for", KW), (" i ", FG), ("in", KW), (" range(len(tokens)):", FG)],
    [("        target = word_dict[tokens[i]]", FG)],
    [("        ", FG), ("for", KW), (" j ", FG), ("in", KW), (" range(max(", FG), ("0", NUM), (", i - window_size),", FG)],
    [("                       min(len(tokens), i + window_size + ", FG), ("1", NUM), (")):", FG)],
    [("            ", FG), ("if", KW), (" i != j:", FG)],
    [("                context = word_dict[tokens[j]]", FG)],
    [("                skip_grams.append([target, context])", FG)],
])

# Step 3
render("code_step3.png", [
    [("class", KW), (" Word2Vec", TYPE), ("(nn.Module):", FG)],
    [("    ", FG), ("def", KW), (" ", FG), ("__init__", FUNC), ("(self, vocab_size, embedding_size):", FG)],
    [("        ", FG), ("super", FUNC), ("().__init__()", FG)],
    [("        self.W = nn.Linear(vocab_size, embedding_size, bias=", FG), ("False", KW), (")", FG)],
    [("        self.WT = nn.Linear(embedding_size, vocab_size, bias=", FG), ("False", KW), (")", FG)],
    [("    ", FG), ("def", KW), (" ", FG), ("forward", FUNC), ("(self, X):", FG)],
    [("        hidden_layer = self.W(X)", FG)],
    [("        output_layer = self.WT(hidden_layer)", FG)],
    [("        ", FG), ("return", KW), (" output_layer", FG)],
    [("embedding_size = ", FG), ("2", NUM)],
    [("model = Word2Vec(vocab_size, embedding_size)", FG)],
])

# Step 4
render("code_step4.png", [
    [("criterion = nn.CrossEntropyLoss()", FG)],
    [("optimizer = optim.Adam(model.parameters(), lr=", FG), ("0.01", NUM), (")", FG)],
    [("def", KW), (" ", FG), ("get_one_hot", FUNC), ("(word_idx, vocab_size):", FG)],
    [("    x = torch.zeros(vocab_size)", FG)],
    [("    x[word_idx] = ", FG), ("1.0", NUM)],
    [("    ", FG), ("return", KW), (" x", FG)],
])

# Step 5
render("code_step5.png", [
    [("epochs = ", FG), ("5000", NUM)],
    [("losses = []", FG)],
    [("for", KW), (" epoch ", FG), ("in", KW), (" range(epochs):", FG)],
    [("    loss_val = ", FG), ("0", NUM)],
    [("    ", FG), ("for", KW), (" target, context ", FG), ("in", KW), (" skip_grams:", FG)],
    [("        x = get_one_hot(target, vocab_size)", FG)],
    [("        y_true = torch.tensor([context], dtype=torch.long)", FG)],
    [("        optimizer.zero_grad()", FG)],
    [("        y_pred = model(x)", FG)],
    [("        loss = criterion(y_pred.unsqueeze(", FG), ("0", NUM), ("), y_true)", FG)],
    [("        loss.backward()", FG)],
    [("        optimizer.step()", FG)],
    [("        loss_val += loss.item()", FG)],
    [("    losses.append(loss_val / len(skip_grams))", FG)],
])

# Step 6
render("code_step6.png", [
    [("W_embed = model.W.weight.data.numpy().T", FG)],
    [("plt.figure(figsize=(", FG), ("10", NUM), (", ", FG), ("8", NUM), ("))", FG)],
    [("for", KW), (" i, word ", FG), ("in", KW), (" enumerate(word_list):", FG)],
    [("    x, y = W_embed[i][", FG), ("0", NUM), ("], W_embed[i][", FG), ("1", NUM), ("]", FG)],
    [("    plt.scatter(x, y)", FG)],
    [("    plt.annotate(word, (x, y), xytext=(", FG), ("5", NUM), (", ", FG), ("2", NUM), ("),", FG)],
    [("                 textcoords=", FG), ("'offset points'", STR), (", fontsize=", FG), ("12", NUM), (")", FG)],
    [("plt.title(", FG), ('"Word2Vec (Skip-gram) Embedding Results"', STR), (")", FG)],
    [("plt.show()", FG)],
])

# Step 7
render("code_step7.png", [
    [("tuning_embedding_size = ", FG), ("10", NUM)],
    [("tuning_window_size = ", FG), ("2", NUM)],
    [("tuning_epochs = ", FG), ("3000", NUM)],
    [("# 데이터 재구성 (window_size 반영)", COMMENT)],
    [("tuning_skip_grams = []", FG)],
    [("# (생략) skip_grams 재생성 후 모델/옵티마이저 새로 초기화", COMMENT)],
    [("tuning_model = Word2Vec(vocab_size, tuning_embedding_size)", FG)],
    [("tuning_optimizer = optim.Adam(tuning_model.parameters(), lr=", FG), ("0.01", NUM), (")", FG)],
    [("# 학습 루프 후 Loss 비교 시각화", COMMENT)],
])

# 출력 결과 텍스트 박스들 (검은 배경)
def render_output(filename, text_lines, width_in=8.0, fontsize=10):
    h = 0.26 * len(text_lines) + 0.3
    fig, ax = plt.subplots(figsize=(width_in, h))
    fig.patch.set_facecolor('#0c0c0c')
    ax.set_facecolor('#0c0c0c')
    ax.set_xlim(0, 1); ax.set_ylim(0, len(text_lines)+0.4)
    ax.axis('off')
    for i, line in enumerate(text_lines):
        y = len(text_lines) - i - 0.3
        ax.text(0.02, y, line, color='#cccccc', family='Consolas', fontsize=fontsize, va='center')
    plt.tight_layout(pad=0.2)
    plt.savefig(os.path.join(OUT, filename), dpi=160, facecolor='#0c0c0c', bbox_inches='tight')
    plt.close()

render_output("out_step1.png", [
    "단어 사전 크기: 15",
    "단어-인덱스 매핑: {'japan': 0, 'korea': 1, 'he': 2, 'tokyo': 3,",
    "  'france': 4, 'queen': 5, 'seoul': 6, 'is': 7, 'paris': 8,",
    "  'she': 9, 'man': 10, 'king': 11, 'a': 12, 'capital': 13,",
    "  'woman': 14}",
])
render_output("out_step2.png", [
    "생성된 학습 데이터 개수: 42",
    "첫 5개 데이터 (Target, Context):",
    "  [[2, 7], [7, 2], [7, 12], [12, 7], [12, 11]]",
])
render_output("out_step4.png", [
    "One-hot vector for index 0:",
    "tensor([1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.])",
])
render_output("out_step5.png", [
    "Epoch:    0, Loss: 2.7076",
    "Epoch: 1000, Loss: 1.1430",
    "Epoch: 2000, Loss: 1.1416",
    "Epoch: 3000, Loss: 1.1409",
    "Epoch: 4000, Loss: 1.1403",
])
render_output("out_step7.png", [
    "Tuned Model Final Loss: (학습 결과 자동 기록)",
    "Window=2, Embed=10 → 학습쌍 70개 (기존 42개 대비 +67%)",
])

print("Code snippets and outputs rendered.")
