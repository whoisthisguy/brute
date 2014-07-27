from grab.spider import Spider, Task, Data
from grab.tools.logs import default_logging
from grab import Grab
import pymongo
from hashlib import sha1
import os
from grab.tools.rex import rex_cache

db = pymongo.Connection()['bestflashgames']

class FlashSpider(Spider):
    initial_urls = ['http://www.bestflashgames.com/categorieslist/']

    def prepare(self):
        self.parsed_games = []

    def get_id(self, url):
        return url.rstrip('/').split('/')[-1]

    def task_initial(self, grab, task):
        for url in grab.tree.xpath('//div[@class="figure"]/a/@href'):
            yield Task('category', url=grab.make_url_absolute(url))

    def task_category(self, grab, task):
        # Integrity
        cid = self.get_id(task.url)
        category = {'_id': cid}
        category = db.category.find_one(category) or category
        category['title'] = grab.css_text('.gallery b font')

        # Save, logging
        db.category.save(category)
        print category['title']

        # Task to parse list of games
        yield Task('category_page', url=task.url, category=category)

    def task_category_page(self, grab, task):
        # Games list
        for url in grab.tree.xpath('//div[@class="figure"]/a/@href'):
            url = grab.make_url_absolute(url, resolve_base=True)
            yield Task('game', url=url, category=task.category)

        ## Next page
        nav = grab.css('.navigation-list a.right', None)
        if nav is not None:
            yield Task(
               'category_page',
               url=grab.make_url_absolute(nav.get('href'), resolve_base=True),
               category=task.category)

    def task_game(self, grab, task):
        # Integrity
        if grab.xpath_exists('//strong[contains(text(), "Not found")]'):
            print 'GAME NOT FOUND'
            return
        gid = self.get_id(task.url)
        game = {'_id': gid}
        if game['_id'] in self.parsed_games:
            print 'Already parsed in this session'
            return
        game = db.game.find_one(game) or game
        game['title'] = grab.css_text('.head p span')

        # Parse categories
        cats = grab.tree.xpath('//div[@class="head"]/ul[1]/li/a/@href')
        game['categories'] = [self.get_id(x) for x in cats]
        game['description'] = grab.xpath_text(
            '//div[@class="post"]/b[text()="Description:"]/../text()', '')
        game['image_url'] = grab.xpath_text('//div[@class="code"]//img/@src', '')
        game['gameid'] = grab.rex_text(rex_cache('gameid=(\d+)'))
        game['url'] = task.url

        # Logging
        print 'GAME', game['title']
        print game['categories']
        print game['description']
        print game['image_url']

        # Save
        db.game.save(game)
        self.parsed_games.append(game['_id'])

        # Task to save game's image
        if not 'image' in game:
            yield Task('game_image', url=game['image_url'], game=game,
                       disable_cache=True)

        yield Task('swf', url='http://www.bestflashgames.com/site/getgame.php?id=%s' % game['gameid'],
                   game=game)

    def task_game_image(self, grab, task):
        # Show activity
        print 'DOWNLOAD %s' % task.url

        # Calculate hash from URL
        img_hash = sha1(task.url).hexdigest()
        img_dir = 'static/game/%s/%s' % (img_hash[:2], img_hash[2:4])

        # Prepare directory
        try:
            os.makedirs(img_dir)
        except OSError:
            pass

        # Find extension
        ext = task.url.split('.')[-1]
        if len(ext) > 4:
            ext = 'bin'

        # Save file
        img_path = os.path.join(img_dir, '%s.%s' % (img_hash, ext))
        grab.response.save(img_path)

        task.game['image'] = img_path
        db.game.save(task.game)

    def task_swf(self, grab, task):
        print 'SWF GATE', task.url
        try:
            url = grab.rex_text(rex_cache(
                'show_flash\(\'([^\']+)'))
        except IndexError:
            try:
                url = grab.rex_text(rex_cache(
                    'name="movie" value="(http://[^"]+)'))
            except IndexError:
                try:
                    url = grab.rex_text(rex_cache(
                        '<embed src="(http[^"]+)'))
                except IndexError, ex:
                    try:
                        url = grab.rex_text(rex_cache(
                            '<iframe src="(http[^"]+)'))
                    except IndexError, ex:
                        url = ''


        task.game['swf'] = url
        db.game.save(task.game)


class SwfSizeSpider(FlashSpider):
    initial_urls = None
    size = 0

    def task_generator(self):
        for game in db.game.find({'swf': {'$ne': ''}}):
            g = Grab()
            g.setup(url=game['swf'], method='head')
            yield Task('swf', grab=g, game=game, disable_cache=True)

    def task_swf(self, grab, task):
        size = int(grab.response.headers.get('Content-Length', 0))
        task.game['swf_size'] = size
        db.game.save(task.game)
        print size

    def shutdown(self):
        print 'Total size', self.size / float((1024 * 1024))




if __name__ == '__main__':
    default_logging()
    bot = SwfSizeSpider(
        thread_number=10)
    #bot.setup_proxylist('var/proxy.txt', 'http', auto_change=True)
    try:
        bot.run()
    except KeyboardInterrupt:
        pass
    print bot.render_stats()
