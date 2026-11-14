// ============================================================================
// SOFT WARM-UP: change the topic below to your niche, then save and import.
// Use several related words: the script watches reels that mention any of them
// and skips the rest, e.g. "fitness, gym, workout, training, protein"
const TOPIC = "fitness, gym, workout, training, protein";
// ============================================================================

/**
 * Instagram soft warm-up: passive use only, steered toward your topic.
 *
 * Checks notifications and messages, watches a few stories and scrolls the
 * feed. Then it searches your topic, looks at a few accounts from the
 * results, and watches reels from the topic's own results page (most of the
 * session). After that it moves to the normal Reels feed, watching reels
 * whose caption or hashtags mention your topic and skipping the rest.
 *
 * Never likes, follows, saves, comments or posts.
 */

// ============================================================================
// Warm-up engine. Everything below is shared by the week 1 and daily scripts;
// only the plan at the bottom of each file differs.
// ============================================================================

async function runWarmup({ page, inputs, log }, makePlan) {
  const rnd = (a, b) => a + Math.random() * (b - a);
  const int = (a, b) => Math.floor(rnd(a, b + 1));
  const chance = p => Math.random() < p;
  const wait = ms => page.waitForTimeout(Math.round(ms));
  const note = t => log(new Date().toLocaleTimeString() + "  " + t);
  const shuffle = list => list.map(v => [Math.random(), v]).sort((a, b) => a[0] - b[0]).map(x => x[1]);

  class Blocked extends Error {}
  const done = { reels: 0, likes: 0, visits: 0, follows: 0, saves: 0, stories: 0, threads: 0 };
  let followsStopped = false;

  // ---------- safety ----------

  // only look at instagram's own warnings (challenge pages, popups, toasts),
  // never at captions or comments, which can contain the same words
  const checkInstagram = async () => {
    const warning = await page.evaluate(() => {
      if (/\/(challenge|accounts\/suspended|accounts\/disabled)/.test(location.pathname)) return true;
      const boxes = Array.from(document.querySelectorAll('[role="dialog"], [role="alertdialog"], [role="alert"]'))
        .filter(el => !el.querySelector("video, article, main a[href*='/p/']") && !el.querySelector('svg[aria-label="Like"]'));
      return /try again later|we limit how often|your account (has been|was) suspended|confirm it's you|help us confirm|unusual activity/i
        .test(boxes.map(el => el.innerText).join("\n"));
    });
    if (warning) throw new Blocked("instagram showed a limit or challenge");
  };

  const stopFollows = reason => {
    if (!followsStopped) note("RED FLAG: " + reason + ". No more follows today, browsing and likes only.");
    followsStopped = true;
  };

  // close the "turn on notifications" style popups instagram throws at new accounts
  const dismissPopups = async () => {
    const notNow = page.getByRole("button", { name: /^not now$/i });
    if (await notNow.count() && await notNow.first().isVisible().catch(() => false)) {
      await wait(rnd(800, 2000));
      await notNow.first().click().catch(() => {});
      await wait(rnd(800, 1500));
    }
  };

  // mark the matching element closest to the middle of the screen, so we act
  // on the reel or post the "person" is actually looking at
  const markInView = async (kind) => page.evaluate((kind) => {
    document.querySelectorAll("[data-warm]").forEach(e => e.removeAttribute("data-warm"));
    // full-size icons only: the small (12px) hearts next to comments are likes for the comment
    const iconButton = label => Array.from(document.querySelectorAll(`svg[aria-label="${label}"]`))
      .filter(svg => svg.getBoundingClientRect().width >= 20)
      .map(svg => svg.closest('[role="button"], button')).filter(Boolean);
    const candidates = {
      like: () => iconButton("Like"),
      save: () => iconButton("Save"),
      comment: () => iconButton("Comment"),
      author: () => Array.from(document.querySelectorAll("main a[href]"))
        .filter(a => /^\/[^/]+\/(reels\/)?$/.test(a.getAttribute("href")) && a.innerText.trim()),
    }[kind]();
    // never like, save or open comments on an ad: find the post the button
    // belongs to (a feed article, or the nearest parent holding the reel's video)
    const isAd = el => {
      let box = el.closest("article");
      if (!box) { box = el; for (let i = 0; i < 12 && box && !box.querySelector("video"); i++) box = box.parentElement; }
      // a parent holding several videos means we climbed past the reel itself
      if (!box || (!box.matches("article") && box.querySelectorAll("video").length !== 1)) return false;
      return /^(ad|sponsored)$/im.test(box.innerText || "");
    };
    const mid = innerHeight / 2;
    let best = null, bestDistance = Infinity;
    for (const el of candidates) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight) continue;
      if (kind !== "author" && isAd(el)) continue;
      const d = Math.abs((r.top + r.bottom) / 2 - mid);
      if (d < bestDistance) { best = el; bestDistance = d; }
    }
    if (!best) return null;
    best.setAttribute("data-warm", kind);
    return best.getAttribute("href") || "ok";
  }, kind);

  const iconLabelOf = loc => loc.locator("svg[aria-label]").first().getAttribute("aria-label").catch(() => null);

  // ---------- getting around ----------

  const openSection = async (href, url) => {
    const link = page.locator(`a[href="${href}"]`).first();
    if (await link.count()) await link.click();
    else await page.goto(url, { waitUntil: "domcontentloaded" });
    await wait(rnd(3000, 6000));
    await dismissPopups();
    await checkInstagram();
  };

  const checkNotifications = async () => {
    const bell = page.getByRole("link", { name: "Notifications" }).first();
    if (!await bell.count()) return;
    await bell.click();
    await wait(rnd(3000, 8000));
    await page.mouse.wheel(0, Math.round(rnd(100, 400)));
    await wait(rnd(1500, 4000));
    // the panel replaces the menu and closes with its own Close button
    const close = page.getByRole("button", { name: "Close" }).first();
    if (await close.count()) await close.click().catch(() => {});
    else await page.keyboard.press("Escape");
    await wait(rnd(1000, 2500));
    note("checked notifications");
  };

  const checkMessages = async () => {
    await openSection("/direct/inbox/", "https://www.instagram.com/direct/inbox/");
    await wait(rnd(3000, 9000));
    note("checked messages (reply to any real DMs yourself)");
  };

  const scrollFeed = async (seconds) => {
    await openSection("/", "https://www.instagram.com/");
    const until = Date.now() + seconds * 1000;
    while (Date.now() < until) {
      await page.mouse.wheel(0, Math.round(rnd(300, 900)));
      await wait(rnd(800, 3500));
      if (chance(0.18)) await wait(rnd(4000, 10000));
      if (chance(0.12)) { await page.mouse.wheel(0, -Math.round(rnd(150, 400))); await wait(rnd(1200, 3000)); }
    }
    note("scrolled the feed for " + Math.round(seconds) + "s");
  };

  const watchStories = async (count) => {
    await openSection("/", "https://www.instagram.com/");
    await page.evaluate(() => scrollTo(0, 0));
    const tray = page.locator('[role="button"][aria-label^="Story by"], button[aria-label^="Story by"]');
    if (!await tray.count()) { note("no stories to watch yet"); return; }
    await tray.first().click();
    await wait(rnd(4000, 8000));
    for (let i = 0; i < count; i++) {
      done.stories++;
      await wait(rnd(3000, 9000));
      if (i < count - 1) await page.keyboard.press("ArrowRight");
    }
    await page.keyboard.press("Escape");
    await wait(rnd(1500, 3000));
    note("watched " + count + " stories");
  };

  // ---------- actions on the reel in view ----------

  const likeInView = async () => {
    if (!await markInView("like")) return false;
    const button = page.locator('[data-warm="like"]');
    await button.click();
    await wait(rnd(1500, 3000));
    if (await iconLabelOf(button) !== "Unlike") { note("a like did not stick, stopping likes"); return "failed"; }
    done.likes++;
    return true;
  };

  const saveInView = async () => {
    if (!await markInView("save")) return false;
    const button = page.locator('[data-warm="save"]');
    await button.click();
    await wait(rnd(1500, 3000));
    if (await iconLabelOf(button) === "Save") return false;
    done.saves++;
    return true;
  };

  const readCommentsInView = async () => {
    if (!await markInView("comment")) return false;
    const reel = page.url();
    await page.locator('[data-warm="comment"]').click();
    await wait(rnd(3000, 6000));
    for (let i = int(1, 3); i > 0; i--) { await page.mouse.wheel(0, Math.round(rnd(200, 500))); await wait(rnd(2000, 5000)); }
    await page.keyboard.press("Escape");
    await wait(rnd(1000, 2500));
    if (page.url() !== reel && !page.url().includes("/reels/")) { await page.goBack().catch(() => {}); await wait(rnd(2000, 4000)); }
    done.threads++;
    return true;
  };

  // ---------- profiles and follows ----------

  // read the profile's own follow button (not the header text, which also says "N following")
  const followButton = () => page.locator("header").first()
    .getByRole("button", { name: /^(follow|follow back|following|requested)$/i }).first();

  const followHere = async () => {
    if (/this account is private/i.test(await page.evaluate(() => document.body.innerText))) return "private, skipped";
    const button = followButton();
    if (!await button.count()) return "no follow button";
    const before = (await button.innerText()).trim().toLowerCase();
    if (before !== "follow" && before !== "follow back") return "already " + before;
    await wait(rnd(1500, 4000));
    await button.click();
    // give instagram up to ~10s to confirm, like a person waiting for the button to change
    let after = before;
    for (let i = 0; i < 5 && (after === "follow" || after === "follow back"); i++) {
      await wait(2000);
      after = (await button.innerText().catch(() => "")).trim().toLowerCase();
    }
    if (after === "requested") { stopFollows("'Requested' on a public account"); return "red flag"; }
    if (after !== "following") { stopFollows("follow button stuck on '" + after + "'"); return "red flag"; }
    await checkInstagram();
    done.follows++;
    return "followed";
  };

  // look around a profile like a person would, optionally follow, then come back
  const browseProfile = async (follow) => {
    await wait(rnd(3000, 6000));
    await checkInstagram();
    for (let i = int(1, 3); i > 0; i--) { await page.mouse.wheel(0, Math.round(rnd(200, 600))); await wait(rnd(1500, 4000)); }
    if (chance(0.3)) {
      const post = page.locator('main a[href*="/p/"], main a[href*="/reel/"]').first();
      if (await post.count() && await post.isVisible().catch(() => false)) {
        await post.click(); await wait(rnd(4000, 10000)); await page.keyboard.press("Escape"); await wait(rnd(1000, 2500));
      }
    }
    await page.evaluate(() => scrollTo(0, 0));
    await wait(rnd(1000, 2500));
    if (follow && !followsStopped) return followHere();
    done.visits++;
    return "visited";
  };

  const visitFromReel = async (follow) => {
    const href = await markInView("author");
    if (!href || href === "ok") return;
    const name = href.split("/")[1];
    await page.locator('[data-warm="author"]').click();
    const result = await browseProfile(follow);
    note("profile @" + name + ": " + result);
    await page.goBack().catch(() => {});
    await wait(rnd(2500, 5000));
    if (!page.url().includes("/reels/")) await openSection("/reels/", "https://www.instagram.com/reels/");
  };

  // search the topic, look at a few accounts, follow some of them
  const searchAndFollow = async (topic, follows) => {
    await openSection("/explore/", "https://www.instagram.com/explore/");
    const box = page.getByRole("textbox", { name: /search/i }).first();
    if (!await box.count()) { note("search box not found, skipping search"); return; }
    // the box sits under a clickable layer, so click where it is like a person would
    const spot = await box.boundingBox();
    await page.mouse.click(spot.x + spot.width * rnd(0.3, 0.7), spot.y + spot.height / 2);
    await wait(rnd(800, 2000));
    await page.keyboard.type(topic, { delay: int(90, 220) });
    await wait(rnd(3500, 5500));
    const names = await page.evaluate(() => Array.from(document.querySelectorAll("main a[href]"))
      .map(a => a.getAttribute("href"))
      .filter(h => /^\/[A-Za-z0-9._]+\/$/.test(h) && !/^\/(explore|reels|direct|accounts|p|stories|popular)\/$/.test(h)));
    const own = await page.evaluate(() => {
      const img = document.querySelector('img[alt$="profile picture"]');
      const a = img && img.closest("a");
      return a ? a.getAttribute("href") : "";
    });
    const results = [...new Set(names)].filter(h => h !== own).slice(0, 8);
    note("searched \"" + topic + "\", " + results.length + " accounts in the results");
    const picks = shuffle(results).slice(0, Math.min(results.length, follows + int(1, 2)));
    let followed = 0;
    for (const href of picks) {
      const want = followed < follows && !followsStopped && chance(0.75);
      const link = page.locator(`a[href="${href}"]`).first();
      if (await link.count() && await link.isVisible().catch(() => false)) await link.click();
      else await page.goto("https://www.instagram.com" + href, { waitUntil: "domcontentloaded" });
      const result = await browseProfile(want);
      if (result === "followed") followed++;
      note("profile @" + href.replaceAll("/", "") + ": " + result);
      await page.goBack().catch(() => {});
      await wait(rnd(2500, 5000));
      // never two follows in a row: do something else in between
      if (result === "followed") await wait(rnd(8000, 20000));
      if (followsStopped) break;
    }
  };

  const followingCount = async () => {
    const own = page.locator('a[href^="/"]:has(img[alt$="profile picture"])').first();
    if (!await own.count()) return null;
    await own.click();
    await wait(rnd(3000, 5000));
    const n = await page.evaluate(() => {
      const m = document.body.innerText.replace(/,/g, "").match(/(\d+)\s+following/i);
      return m ? Number(m[1]) : null;
    });
    return n;
  };

  // ---------- topic ----------

  // the reel on screen: its caption, username, audio and hashtags as one piece of text
  const reelInView = () => page.evaluate(() => {
    const mid = innerHeight / 2;
    let best = null, bestDistance = Infinity;
    for (const v of document.querySelectorAll("video")) {
      const r = v.getBoundingClientRect();
      if (!r.height || r.bottom < 0 || r.top > innerHeight) continue;
      const d = Math.abs((r.top + r.bottom) / 2 - mid);
      if (d < bestDistance) { best = v; bestDistance = d; }
    }
    if (!best) return null;
    let box = best;
    while (box.parentElement && box.parentElement.querySelectorAll("video").length === 1) box = box.parentElement;
    const tags = Array.from(box.querySelectorAll('a[href*="/explore/tags/"]')).map(a => a.getAttribute("href"));
    return { text: (box.innerText || "") + " " + tags.join(" "), ad: /^(ad|sponsored)$/im.test(box.innerText || "") };
  });

  // run one of the day's actions on whatever is on screen
  let likesBroken = false;
  const doAction = async (action, inDialog) => {
    if (action === "like" && !likesBroken) likesBroken = await likeInView() === "failed";
    if (action === "save") await saveInView();
    if (action === "thread") {
      if (inDialog) { // comments sit next to the post: scroll through them
        const dialog = await page.locator('[role="dialog"]').first().boundingBox();
        if (dialog) await page.mouse.move(dialog.x + dialog.width * 0.8, dialog.y + dialog.height * 0.5);
        for (let i = int(2, 4); i > 0; i--) { await page.mouse.wheel(0, Math.round(rnd(150, 400))); await wait(rnd(2000, 4500)); }
        done.threads++;
      } else await readCommentsInView();
    }
    if (action === "visit" || action === "follow") {
      const follow = action === "follow" && !followsStopped;
      if (!inDialog) return visitFromReel(follow);
      const author = await page.evaluate(() => {
        const d = document.querySelector('[role="dialog"]');
        const a = d && Array.from(d.querySelectorAll("a[href]")).find(a => /^\/[A-Za-z0-9._]+\/$/.test(a.getAttribute("href")) && a.innerText.trim());
        if (!a) return null;
        a.setAttribute("data-warm", "dialog-author");
        return a.getAttribute("href");
      });
      if (!author) return;
      await page.locator('[data-warm="dialog-author"]').click();
      const result = await browseProfile(follow);
      note("profile @" + author.replaceAll("/", "") + ": " + result);
      return "left";
    }
  };

  // the topic's own results: open a reel from the grid, then keep going to the
  // next one like scrolling a feed. Every reel here is on the topic, so this is
  // where they get watched properly and where the day's actions happen.
  const seenTopic = new Set();
  const topicPage = topic => "https://www.instagram.com/explore/search/keyword/?q=" + encodeURIComponent(topic);
  const openTopicGrid = async (topic) => {
    await page.goto(topicPage(topic), { waitUntil: "domcontentloaded" });
    await wait(rnd(4000, 7000));
    await checkInstagram();
    for (let i = int(0, 3); i > 0; i--) { await page.mouse.wheel(0, Math.round(rnd(250, 600))); await wait(rnd(1200, 3000)); }
    const tiles = page.locator('main a[href*="/p/"], main a[href*="/reel/"]');
    const count = await tiles.count();
    for (let i = 0; i < 10 && count; i++) {
      const tile = tiles.nth(int(0, Math.min(count, 15) - 1));
      if (seenTopic.has(await tile.getAttribute("href"))) continue;
      if (await tile.isVisible().catch(() => false)) { await tile.click(); await wait(rnd(2500, 4000)); return true; }
    }
    return false;
  };

  const watchTopicStream = async (topic, count, queue) => {
    if (!await openTopicGrid(topic)) { note("no posts found for \"" + topic + "\""); return 0; }
    let watched = 0;
    for (let n = 0; (watched < count || queue.length) && n < count * 3; n++) {
      if (!await page.locator('[role="dialog"]').count()) { if (!await openTopicGrid(topic)) break; }
      const path = new URL(page.url()).pathname;
      if (seenTopic.has(path)) { await page.keyboard.press("ArrowRight"); await wait(rnd(1200, 2500)); continue; }
      seenTopic.add(path);
      const reel = await reelInView();
      if (reel && reel.ad) { await wait(rnd(500, 1500)); await page.keyboard.press("ArrowRight"); await wait(rnd(1500, 3000)); continue; }
      watched++;
      done.reels++;
      await wait(Math.random() > 0.85 ? rnd(18000, 35000) : rnd(6000, 16000));
      let share = queue.length / Math.max(1, count - watched);
      let left = false;
      while (queue.length && !left && (share >= 1 || chance(share))) {
        left = await doAction(queue.shift(), true) === "left";
        share -= 1;
        await wait(rnd(1000, 3000));
      }
      if (left) { await openTopicGrid(topic); continue; } // went to a profile: back to the topic grid
      await page.keyboard.press("ArrowRight");
      await wait(rnd(1500, 3000));
      if (n % 8 === 7) await checkInstagram();
    }
    await page.keyboard.press("Escape");
    await wait(rnd(1500, 3000));
    note("watched " + watched + " \"" + topic + "\" reels");
    return watched;
  };

  // ---------- the session ----------

  await page.bringToFront();
  if (!page.url().includes("instagram.com")) {
    await page.goto("https://www.instagram.com/", { waitUntil: "domcontentloaded" });
    await wait(rnd(3000, 6000));
  }
  // only a logged-in account has the Messages link in the menu
  await page.locator('a[href="/direct/inbox/"]').first().waitFor({ timeout: 15000 }).catch(() => {});
  if (!await page.locator('a[href="/direct/inbox/"]').count()) { note("stopped: not logged in to instagram"); return; }

  // every word or phrase in TOPIC counts when deciding if a reel fits;
  // one of them is picked for today's searches
  const topics = String(inputs?.topic || TOPIC || "").split(",").map(s => s.trim().toLowerCase()).filter(Boolean);
  const topic = topics.length ? topics[int(0, topics.length - 1)] : "";
  const fits = text => topics.some(t => text.includes(t) || text.includes(t.replace(/\s+/g, "")));

  try {
    await checkInstagram();
    const plan = await makePlan({ inputs, rnd, int, chance, followingCount, note });
    if (!plan) return;
    note("today: " + plan.reels + " reels, " + plan.likes + " likes, " + plan.visits + " profile visits, " +
         plan.follows + " follows, " + plan.saves + " saves, " + plan.stories + " stories" +
         (plan.threads ? ", " + plan.threads + " comment threads" : ""));
    note(topics.length ? "topic: " + topics.join(", ") : "no topic set, watching reels without filtering");

    // natural flow: notifications -> messages -> stories -> feed -> topic search -> reels -> notifications
    await openSection("/", "https://www.instagram.com/");
    await checkNotifications();
    await checkMessages();
    if (plan.stories) await watchStories(plan.stories);
    await scrollFeed(rnd(40, 120));

    // the day's actions, never two follows back to back
    let followsLeft = plan.follows;
    if (topic) {
      await searchAndFollow(topic, plan.follows ? Math.min(plan.follows, int(1, 2)) : 0);
      followsLeft = Math.max(0, plan.follows - done.follows);
    }
    const queue = shuffle([
      ...Array(plan.likes).fill("like"),
      ...Array(plan.visits).fill("visit"),
      ...Array(followsLeft).fill("follow"),
      ...Array(plan.saves).fill("save"),
      ...Array(plan.threads || 0).fill("thread"),
    ]);
    for (let i = 1; i < queue.length; i++) {
      if (queue[i] === "follow" && queue[i - 1] === "follow") {
        const swap = queue.findIndex((a, j) => j > i && a !== "follow");
        if (swap > -1) [queue[i], queue[swap]] = [queue[swap], queue[i]];
      }
    }
    // most reels come from the topic, where every one fits and all the actions happen
    let fromTopic = 0;
    if (topic) fromTopic = await watchTopicStream(topic, Math.round(plan.reels * rnd(0.55, 0.75)), queue);

    // the rest from the normal Reels feed: watch the ones that fit, skip the others
    const feedReels = plan.reels - fromTopic;
    await openSection("/reels/", "https://www.instagram.com/reels/");
    let watched = 0, skipped = 0;
    for (let n = 0; watched < feedReels && n < feedReels + 15; n++) {
      await wait(rnd(1200, 2500));
      const reel = await reelInView();
      const good = reel && !reel.ad && (!topics.length || fits(reel.text.toLowerCase()));
      if (!good) {
        skipped++;
        await wait(rnd(300, 1800));
      } else {
        watched++;
        done.reels++;
        const roll = Math.random();
        if (topics.length) await wait(roll > 0.85 ? rnd(18000, 35000) : rnd(6000, 16000));
        else await wait(roll < 0.25 ? rnd(1000, 2500) : roll > 0.9 ? rnd(15000, 30000) : rnd(4000, 12000));
        let share = queue.length / Math.max(1, feedReels - watched + 1);
        while (queue.length && (share >= 1 || chance(share))) {
          await doAction(queue.shift(), false);
          share -= 1;
          await wait(rnd(1000, 3000));
        }
      }
      await page.keyboard.press("ArrowDown");
      await wait(rnd(600, 1500));
      if (n % 8 === 7) await checkInstagram();
    }
    if (topics.length) note("reels feed: watched " + watched + " that fit the topic, skipped " + skipped + " that did not");
    if (queue.length) note(queue.length + " actions left over for another day");

    await openSection("/", "https://www.instagram.com/");
    await checkNotifications();
    note("done");
  } catch (error) {
    if (!(error instanceof Blocked)) throw error;
    note("STOPPED: " + error.message + ". Leave this account alone for today.");
  }

  note("did: " + done.reels + " reels, " + done.likes + " likes, " + done.visits + " profile visits, " +
       done.follows + " follows, " + done.saves + " saves, " + done.stories + " stories" +
       (done.threads ? ", " + done.threads + " comment threads" : "") +
       (followsStopped ? " (follows stopped by a red flag)" : ""));
}

export default async function softWarmup(ctx) {
  await runWarmup(ctx, async ({ int, chance }) => ({
    reels: int(18, 27),
    visits: int(2, 5),
    likes: 0,
    follows: 0,
    saves: 0,
    stories: int(1, 3),
    threads: chance(0.3) ? 1 : 0,
  }));
}
