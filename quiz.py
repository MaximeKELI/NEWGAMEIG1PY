import pygame
import sys
import random
import json
import base64
import io
from pygame import mixer

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
MAX_PLAYERS = 4
QUESTIONS_PER_PLAYER = 5
MAX_OPTIONS = 4
MAX_NAME_LENGTH = 20
QUESTION_TIME_LIMIT = 30

SOUNDS = {
    'correct': '',
    'wrong': '',
    'timer': ''
}

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
DARK_BLUE = (0, 0, 50)
LIGHT_BLUE = (100, 100, 255)

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.correct_answers = 0
        self.current_question_index = 0
        self.question_indices = []

class Question:
    def __init__(self, question, options, correct_answer, category="Général"):
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.category = category
        self.used = False

class QuizGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Quiz Informatique")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        self.players = []
        self.current_player = 0
        self.questions = []
        self.num_players = 0
        self.game_state = "MENU"
        self.time_left = QUESTION_TIME_LIMIT
        self.timer_start = 0
        
        self.sounds = {
            'correct': mixer.Sound(buffer=bytearray([128]*1000)),
            'wrong': mixer.Sound(buffer=bytearray([64,128]*500)),
            'timer': mixer.Sound(buffer=bytearray([80]*2000))
        }
        
        self._init_questions()
    
    def _init_questions(self):
        self.questions = [
            Question("Quel langage a inspiré C++?", ["C","Java","Python","Assembly"],0),
            Question("Commande Linux pour lister les fichiers?", ["dir","ls","list","show"],1),
            Question("Gestionnaire de paquets Python?", ["pip","npm","apt","yum"],0)
        ]
        
        try:
            with open("questions.json", "r") as f:
                data = json.load(f)
                for item in data:
                    self.questions.append(Question(
                        item["question"],
                        item["options"],
                        item["correct_answer"],
                        item.get("category", "Général")
                    ))
        except:
            pass
    
    def _assign_questions(self):
        available = [i for i, q in enumerate(self.questions) if not q.used]
        for player in self.players:
            player.question_indices = random.sample(available, min(QUESTIONS_PER_PLAYER, len(available)))
            player.current_question_index = 0
    
    def _render_text(self, text, pos, color, font=None, center=False):
        font = font or self.font
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = pos
        else:
            text_rect.topleft = pos
        self.screen.blit(text_surface, text_rect)
        return text_rect
    
    def _draw_button(self, text, pos, size, color, hover_color):
        rect = pygame.Rect(pos, size)
        mouse_pos = pygame.mouse.get_pos()
        current_color = hover_color if rect.collidepoint(mouse_pos) else color
        pygame.draw.rect(self.screen, current_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=8)
        self._render_text(text, rect.center, WHITE, center=True)
        return rect
    
    def _show_menu(self):
        start_btn = help_btn = quit_btn = None
        
        while self.game_state == "MENU":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.game_state = "PLAYER_SELECT"
                    elif event.key == pygame.K_2:
                        self._show_help()
                    elif event.key == pygame.K_3:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if start_btn and start_btn.collidepoint(event.pos):
                        self.game_state = "PLAYER_SELECT"
                    elif help_btn and help_btn.collidepoint(event.pos):
                        self._show_help()
                    elif quit_btn and quit_btn.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
            
            self.screen.fill(DARK_BLUE)
            self._render_text("QUIZ INFORMATIQUE", (SCREEN_WIDTH//2, 100), GOLD, self.large_font, True)
            
            start_btn = self._draw_button("1. Commencer", (SCREEN_WIDTH//2 - 150, 200), (300, 50), BLUE, LIGHT_BLUE)
            help_btn = self._draw_button("2. Aide", (SCREEN_WIDTH//2 - 150, 270), (300, 50), BLUE, LIGHT_BLUE)
            quit_btn = self._draw_button("3. Quitter", (SCREEN_WIDTH//2 - 150, 340), (300, 50), RED, (255, 100, 100))
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def _show_help(self):
        showing = True
        while showing:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    showing = False
            
            self.screen.fill(DARK_BLUE)
            self._render_text("AIDE", (SCREEN_WIDTH//2, 50), GOLD, self.large_font, True)
            
            lines = [
                "Comment jouer:",
                "- 2-4 joueurs",
                "- Répondez aux questions",
                "- Bonne réponse: +10 points",
                "- Utilisez 1-4 pour répondre",
                "- Échap: Retour au menu"
            ]
            
            for i, line in enumerate(lines):
                self._render_text(line, (100, 120 + i * 30), WHITE, self.small_font)
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def _select_players(self):
        selecting = True
        player_btns = []
        
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_2 <= event.key <= pygame.K_4:
                        self.num_players = event.key - pygame.K_0
                        selecting = False
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = "MENU"
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for i, btn in enumerate(player_btns, 2):
                        if btn.collidepoint(event.pos):
                            self.num_players = i
                            selecting = False
            
            self.screen.fill(DARK_BLUE)
            self._render_text("Nombre de joueurs", (SCREEN_WIDTH//2, 50), GOLD, self.large_font, True)
            
            player_btns = []
            for i in range(2, 5):
                btn = self._draw_button(f"{i} Joueurs", (SCREEN_WIDTH//2 - 150, 100 + i * 60), (300, 50), BLUE, LIGHT_BLUE)
                player_btns.append(btn)
            
            back_btn = self._draw_button("Retour", (SCREEN_WIDTH//2 - 150, 400), (300, 50), RED, (255, 100, 100))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        self._get_player_names()
    
    def _get_player_names(self):
        current = 0
        input_text = ""
        
        while current < self.num_players:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text:
                        self.players.append(Player(input_text))
                        current += 1
                        input_text = ""
                    elif event.key == pygame.K_ESCAPE:
                        self.players = []
                        self.game_state = "PLAYER_SELECT"
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif len(input_text) < MAX_NAME_LENGTH and event.unicode.isprintable():
                        input_text += event.unicode
            
            self.screen.fill(DARK_BLUE)
            prompt = f"Joueur {current + 1} - Entrez votre nom:"
            self._render_text(prompt, (SCREEN_WIDTH//2, 150), WHITE, center=True)
            
            input_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 200, 300, 40)
            pygame.draw.rect(self.screen, WHITE, input_rect, 2)
            self._render_text(input_text, (input_rect.x + 10, input_rect.y + 10), WHITE)
            
            if pygame.time.get_ticks() % 1000 < 500:
                cursor_x = input_rect.x + 10 + self.font.size(input_text)[0]
                pygame.draw.line(self.screen, WHITE, (cursor_x, input_rect.y + 5), (cursor_x, input_rect.y + 35), 2)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        self._assign_questions()
        self.game_state = "GAME"
    
    def _show_question(self):
        player = self.players[self.current_player]
        
        if player.current_question_index >= len(player.question_indices):
            self.current_player = (self.current_player + 1) % self.num_players
            if self.current_player == 0:
                self._show_results()
            return
        
        q_idx = player.question_indices[player.current_question_index]
        question = self.questions[q_idx]
        
        if player.current_question_index == 0 or self.time_left <= 0:
            self.timer_start = pygame.time.get_ticks()
            self.time_left = QUESTION_TIME_LIMIT
            self.sounds['timer'].play(-1)
        
        current_time = pygame.time.get_ticks()
        self.time_left = max(0, QUESTION_TIME_LIMIT - (current_time - self.timer_start) // 1000)
        
        answered = False
        selected = -1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_4:
                    selected = event.key - pygame.K_1
                    answered = True
                elif event.key == pygame.K_ESCAPE:
                    self.game_state = "MENU"
                    return
        
        self.screen.fill(BLACK)
        self._render_text(f"{player.name} - Score: {player.score}", (20, 20), WHITE)
        
        time_width = (SCREEN_WIDTH - 40) * self.time_left / QUESTION_TIME_LIMIT
        time_color = GREEN if self.time_left > 10 else RED
        pygame.draw.rect(self.screen, time_color, (20, 50, time_width, 10))
        
        self._render_text(question.question, (SCREEN_WIDTH//2, 150), WHITE, self.large_font, True)
        
        for i, option in enumerate(question.options):
            self._render_text(f"{i+1}. {option}", (SCREEN_WIDTH//2, 220 + i * 60), WHITE, center=True)
        
        pygame.display.flip()
        
        if answered:
            self.sounds['timer'].stop()
            
            if selected == question.correct_answer:
                player.score += 10
                player.correct_answers += 1
                feedback = "Bonne réponse! +10 points"
                color = GREEN
                self.sounds['correct'].play()
            else:
                feedback = f"Mauvaise réponse! La bonne réponse était: {question.options[question.correct_answer]}"
                color = RED
                self.sounds['wrong'].play()
            
            self.screen.fill(BLACK)
            self._render_text(feedback, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), color, center=True)
            pygame.display.flip()
            pygame.time.delay(2000)
            
            player.current_question_index += 1
            self.current_player = (self.current_player + 1) % self.num_players
    
    def _show_results(self):
        max_score = max(p.score for p in self.players)
        winners = [p for p in self.players if p.score == max_score]
        
        showing = True
        while showing:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    showing = False
                    self.__init__()
            
            self.screen.fill(DARK_BLUE)
            self._render_text("Résultats Finaux", (SCREEN_WIDTH//2, 50), GOLD, self.large_font, True)
            
            y_pos = 120
            for i, player in enumerate(sorted(self.players, key=lambda p: -p.score)):
                score_width = int((SCREEN_WIDTH - 200) * (player.score / max(1, max_score)))
                pygame.draw.rect(self.screen, BLUE, (100, y_pos + 20, score_width, 30))
                
                player_text = f"{i+1}. {player.name}: {player.score} pts"
                color = GOLD if player in winners else WHITE
                self._render_text(player_text, (110, y_pos + 25), color)
                
                y_pos += 70
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def run(self):
        while True:
            if self.game_state == "MENU":
                self._show_menu()
            elif self.game_state == "PLAYER_SELECT":
                self._select_players()
            elif self.game_state == "GAME":
                self._show_question()
            
            self.clock.tick(60)

if __name__ == "__main__":
    game = QuizGame()
    game.run()