/**
 * 游戏结束界面
 */

export class GameOver {
    constructor(onRestartCallback) {
        this.container = null;
        this.onRestart = onRestartCallback;
        this.scoreText = null;
        this.bestScoreText = null;
    }

    create() {
        this.container = new Laya.Sprite();
        Laya.stage.addChild(this.container);
        
        // 半透明背景
        const bg = new Laya.Sprite();
        bg.graphics.drawRect(0, 0, Laya.stage.width, Laya.stage.height, "#000000");
        bg.alpha = 0.8;
        this.container.addChild(bg);
        
        // 游戏结束文字
        const gameOverText = new Laya.Text();
        gameOverText.text = "游戏结束";
        gameOverText.font = "Arial Black";
        gameOverText.fontSize = 80;
        gameOverText.color = "#FF4444";
        gameOverText.bold = true;
        gameOverText.x = Laya.stage.width / 2 - 160;
        gameOverText.y = 250;
        gameOverText.stroke = 4;
        gameOverText.strokeColor = "#000000";
        this.container.addChild(gameOverText);
        
        // 分数显示
        const scoreLabel = new Laya.Text();
        scoreLabel.text = "得分";
        scoreLabel.font = "Arial";
        scoreLabel.fontSize = 30;
        scoreLabel.color = "#AAAAAA";
        scoreLabel.x = Laya.stage.width / 2 - 50;
        scoreLabel.y = 380;
        this.container.addChild(scoreLabel);
        
        this.scoreText = new Laya.Text();
        this.scoreText.text = "0";
        this.scoreText.font = "Arial Black";
        this.scoreText.fontSize = 60;
        this.scoreText.color = "#FFFFFF";
        this.scoreText.bold = true;
        this.scoreText.x = Laya.stage.width / 2 - 30;
        this.scoreText.y = 420;
        this.container.addChild(this.scoreText);
        
        // 最高分
        const bestLabel = new Laya.Text();
        bestLabel.text = "最高分";
        bestLabel.font = "Arial";
        bestLabel.fontSize = 24;
        bestLabel.color = "#888888";
        bestLabel.x = Laya.stage.width / 2 - 50;
        bestLabel.y = 520;
        this.container.addChild(bestLabel);
        
        this.bestScoreText = new Laya.Text();
        this.bestScoreText.text = "0";
        this.bestScoreText.font = "Arial Black";
        this.bestScoreText.fontSize = 40;
        this.bestScoreText.color = "#FFD700";
        this.bestScoreText.bold = true;
        this.bestScoreText.x = Laya.stage.width / 2 - 20;
        this.bestScoreText.y = 550;
        this.container.addChild(this.bestScoreText);
        
        // 重新开始按钮
        const restartBtn = new Laya.Sprite();
        restartBtn.graphics.drawRoundRect(0, 0, 200, 60, 10, 10, "#4CAF50");
        restartBtn.x = Laya.stage.width / 2 - 100;
        restartBtn.y = 650;
        restartBtn.on(Laya.Event.MOUSE_DOWN, this, this.onRestartClick);
        this.container.addChild(restartBtn);
        
        const restartText = new Laya.Text();
        restartText.text = "再来一次";
        restartText.font = "Arial Black";
        restartText.fontSize = 28;
        restartText.color = "#FFFFFF";
        restartText.bold = true;
        restartText.x = restartBtn.x + 35;
        restartText.y = restartBtn.y + 16;
        this.container.addChild(restartText);
        
        // 分享按钮
        const shareBtn = new Laya.Sprite();
        shareBtn.graphics.drawRoundRect(0, 0, 200, 60, 10, 10, "#2196F3");
        shareBtn.x = Laya.stage.width / 2 - 100;
        shareBtn.y = 730;
        shareBtn.on(Laya.Event.MOUSE_DOWN, this, this.onShareClick);
        this.container.addChild(shareBtn);
        
        const shareText = new Laya.Text();
        shareText.text = "分享成绩";
        shareText.font = "Arial Black";
        shareText.fontSize = 28;
        shareText.color = "#FFFFFF";
        shareText.bold = true;
        shareText.x = shareBtn.x + 35;
        shareText.y = shareBtn.y + 16;
        this.container.addChild(shareText);
    }

    show(score) {
        if (!this.container) this.create();
        this.container.visible = true;
        
        // 更新分数
        if (this.scoreText) {
            this.scoreText.text = score.toString();
        }
        
        // 更新最高分
        const bestScore = localStorage.getItem('jump_jump_best') || 0;
        if (score > bestScore) {
            localStorage.setItem('jump_jump_best', score);
            if (this.bestScoreText) {
                this.bestScoreText.text = score.toString();
            }
        } else {
            if (this.bestScoreText) {
                this.bestScoreText.text = bestScore.toString();
            }
        }
    }

    hide() {
        if (this.container) {
            this.container.visible = false;
        }
    }

    onRestartClick(e) {
        e.stopPropagation();
        if (this.onRestart) {
            this.onRestart();
        }
    }

    onShareClick(e) {
        e.stopPropagation();
        alert('分享功能开发中...');
        // TODO: 实现微信分享
    }

    destroy() {
        if (this.container && this.container.parent) {
            this.container.parent.removeChild(this.container);
        }
    }
}
