/**
 * HUD - 游戏界面显示
 * 显示分数、蓄力条等
 */

export class HUD {
    constructor() {
        this.container = null;
        this.scoreText = null;
        this.chargeBar = null;
        this.perfectText = null;
    }

    create() {
        this.container = new Laya.Sprite();
        Laya.stage.addChild(this.container);
        
        // 分数显示
        this.scoreText = new Laya.Text();
        this.scoreText.text = "0";
        this.scoreText.font = "Arial Black";
        this.scoreText.fontSize = 80;
        this.scoreText.color = "#FFFFFF";
        this.scoreText.bold = true;
        this.scoreText.x = 50;
        this.scoreText.y = 50;
        this.scoreText.stroke = 4;
        this.scoreText.strokeColor = "#000000";
        this.container.addChild(this.scoreText);
        
        // 蓄力条（初始隐藏）
        this.chargeBar = new Laya.Sprite();
        this.chargeBar.x = 50;
        this.chargeBar.y = 150;
        this.container.addChild(this.chargeBar);
        
        // 完美提示
        this.perfectText = new Laya.Text();
        this.perfectText.text = "完美!";
        this.perfectText.font = "Arial Black";
        this.perfectText.fontSize = 40;
        this.perfectText.color = "#FFD700";
        this.perfectText.bold = true;
        this.perfectText.x = Laya.stage.width / 2 - 50;
        this.perfectText.y = 300;
        this.perfectText.visible = false;
        this.container.addChild(this.perfectText);
    }

    show() {
        if (!this.container) this.create();
        this.container.visible = true;
    }

    hide() {
        if (this.container) {
            this.container.visible = false;
        }
    }

    updateScore(score) {
        if (this.scoreText) {
            this.scoreText.text = score.toString();
        }
    }

    updateCharge(ratio) {
        if (!this.chargeBar) return;
        
        this.chargeBar.graphics.clear();
        
        // 蓄力条背景
        this.chargeBar.graphics.drawRect(0, 0, 200, 20, "#333333");
        
        // 蓄力条填充
        const width = 200 * ratio;
        let color = "#00FF00";
        if (ratio > 0.5) color = "#FFFF00";
        if (ratio > 0.8) color = "#FF0000";
        
        this.chargeBar.graphics.drawRect(0, 0, width, 20, color);
    }

    showPerfect() {
        if (this.perfectText) {
            this.perfectText.visible = true;
            this.perfectText.alpha = 1;
            
            // 淡出动画
            Laya.timer.frameLoop(1, this, () => {
                this.perfectText.alpha -= 0.05;
                this.perfectText.y -= 2;
                if (this.perfectText.alpha <= 0) {
                    this.perfectText.visible = false;
                    Laya.timer.clear(this, this);
                }
            });
        }
    }

    destroy() {
        if (this.container && this.container.parent) {
            this.container.parent.removeChild(this.container);
        }
        Laya.timer.clear(this, this);
    }
}
