from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, JavascriptException, NoSuchWindowException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.firefox.options import Options
from time import sleep
import logging
import random
import threading

logger = logging.getLogger('Skribbl Bot Logger')

GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google-chrome'
CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'

options = Options()
options.binary_location = GOOGLE_CHROME_PATH
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--headless')


skribbl_url = 'https://skribbl.io'

accept_cookies_remove_script = 'document.getElementById("aip_gdpr_banner").innerHTML = ""; document.getElementById("aip_gdpr_banner").remove(); console.log("Accept Cookies Removed");'

bot = {
        'name_field_id': 'inputName',
        'custom_avatar_random_id': 'buttonAvatarCustomizerRandomize',
        'create_private_room_id':  'buttonLoginCreatePrivate',
        'accept_cookies_id': 'aip_gdpr_continue',
        'accept_cookies_xpath': '//*[@id="aip_gdpr_continue"]',
        'invite_id': 'invite',
        'lobby_rounds_id': 'lobbySetRounds',
        'lobby_draw_time_id': 'lobbySetDrawTime',
        'lobby_custom_words_id': 'lobbySetCustomWords',
        'lobby_custom_words_chk_box_id': 'lobbyCustomWordsExclusive',
        'lobby_start_game_id': 'buttonLobbyPlay',
        'lobby_players_container_id': 'containerLobbyPlayers',
        'lobby_player_class': 'lobbyPlayer',
    }

def get_bot_name():
    return 'ASB ' + str(int(random.random()*1000))


class SkribblBot:

    def __init__(self, rounds, draw_time, required_players, custom_words_list):
        self.name = get_bot_name()
        self.driver = None
        self.rounds = str(rounds)
        self.draw_time = str(draw_time)
        self.required_players = required_players
        self.custom_words_list = custom_words_list
        self.cookies_accepted = False
        self.game_link = None
        self.game_link_lock = threading.Lock()
        self.get_game_link = self._get_game_link

    def accept_cookies(self):
        if self.cookies_accepted:
            return
        try:
            self.driver.execute_script(accept_cookies_remove_script)
            logger.warning('Removed Accept Cookies box')
            self.cookies_accepted = True
        except (JavascriptException, WebDriverException) as e:
            logger.warning('Accept Cookies did not pop up')

    def check_id_exists(self, id):
        try:
            self.driver.find_element_by_id(id)
        except NoSuchElementException:
            return False
        return True
    
    def _get_game_link(self):
        logger.warning('Acquiring game_link_lock for _get_game_link')
        self.game_link_lock.acquire()
        game_link = self.game_link
        self.game_link_lock.release()
        logger.warning('Releasing game_link_lock for _get_game_link')

        return game_link

    def start_game(self):
        start_game_thread = threading.Thread(target=self._start_game)
        start_game_thread.start()
        get_link_thread = threading.Thread(target=self._get_game_link)
        get_link_thread.start()


    def _start_game(self):
        try:
            logger.warning('Acquiring game_link_lock for _start_game')
            self.game_link_lock.acquire()

            logger.warning('Opening Chrome Headless browser')
            self.driver = webdriver.Firefox(executable_path='/app/vendor/geckodriver/geckodriver') # webdriver.PhantomJS() # webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
            logger.warning('Chrome Headless browser opened successfully')

            self.driver.get(skribbl_url)

            self.accept_cookies()
            logger.warning('Website %s opened successfully', skribbl_url)

            bot_name_field = self.driver.find_element_by_id(bot['name_field_id'])
            bot_name_field.send_keys(self.name)

            self.accept_cookies()
            bot_avatar_randomize = self.driver.find_element_by_id(bot['custom_avatar_random_id'])
            bot_avatar_randomize.click()
            logger.warning('Randomized bot avatar successfully')

            self.accept_cookies()
            bot_private_room = self.driver.find_element_by_id(bot['create_private_room_id'])
            bot_private_room.click()
            logger.warning('Private room created successfully')

            if not self.check_id_exists(bot['invite_id']):
                logger.warning('An Advertisement may be playing, Sleeping for 3 seconds')

            sleep(5)

            self.accept_cookies()
            invite_element = self.driver.find_element_by_id(bot['invite_id'])

            logger.warning("Private room has URL: %s", self.game_link)

            self.accept_cookies()
            rounds_selector = Select(self.driver.find_element_by_id(bot['lobby_rounds_id']))
            rounds_selector.select_by_visible_text(self.rounds)
            logger.warning('Rounds set to %s successfully', self.rounds)

            self.accept_cookies()
            draw_time_selector = Select(self.driver.find_element_by_id(bot['lobby_draw_time_id']))
            draw_time_selector.select_by_visible_text(self.draw_time)
            logger.warning('Draw Time set to %s successfully', self.draw_time)

            self.accept_cookies()
            custom_words_cs = ','.join(self.custom_words_list)
            custom_words_text_box = self.driver.find_element_by_id(bot['lobby_custom_words_id'])
            custom_words_text_box.send_keys(custom_words_cs)
            logger.warning('Custom words filled inside the text box')

            self.accept_cookies()
            custom_words_only = self.driver.find_element_by_id(bot['lobby_custom_words_chk_box_id'])
            custom_words_only.click()
            logger.warning('Room set to use custom words only')

            self.game_link = invite_element.get_attribute('value')
            self.game_link_lock.release()
            logger.warning('Releasing game_link_lock for _start_game')


            players_in_room = 0
            while(True):
                lobby_players_container = self.driver.find_element_by_id(bot['lobby_players_container_id'])
                lobby_players = lobby_players_container.find_elements_by_class_name(bot['lobby_player_class'])
                players_in_room = len(lobby_players) - 1
                logger.warning('%d Players are in room with bot: %s', players_in_room, self.name)
                if players_in_room >= self.required_players:
                    logger.warning('Required playes have entered the room')
                    break
                sleep(5)

            self.accept_cookies()
            start_game_button = self.driver.find_element_by_id(bot['lobby_start_game_id'])
            start_game_button.click()
            logger.warning('Starting the game with %d players', players_in_room)

            sleep(2)

            self.driver.close()
            logger.warning('Bot removed from the private room')
            logger.warning('Game has started')

        except Exception as e:
            logger.warning('Accept Cookies occured abruptly or something else. Restarting the process')
            logger.warning(e)
            try:
                self.game_link_lock.release()
            except Exception:
                logger.warning('Cannot release lock. Maybe never acquired')
            self.driver.close()
            self._start_game()


if __name__ == '__main__':
    skribbl_bot = SkribblBot(6, 90, 1, ['a','b','c','d','e'])
    skribbl_bot.start_game()
    game_link = skribbl_bot.get_game_link()
    print(game_link)