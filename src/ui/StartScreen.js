/**
 * 开始界面
 */

export class StartScreen {
    constructor(onStartCallback) {
        this.container = null;
        this.onStart = onStartCallback;
    }

    create() {
        this.container = new Laya.Sprite();
        Laya.stage.addChild(this.container);
        
        // 半透明背景
        const bg = new Laya.Sprite();
        bg.graphics.drawRect(0, 0, Laya.stage.width, Laya.stage.height, "#000000");
        bg.alpha = 0.7;
        this.container.addChild(bg);
        
        // 游戏标题
        const title = new Laya.Text();
        title.text = "跳一跳";
        title.font = "Arial Black";
        title.fontSize = 100;
        title.color = "#FFFFFF";
        title.bold = true;
        title.x = Laya.stage.width / 2 - 150;
        title.y = 300;
        title.stroke = 4;
        title.strokeColor = "#333333";
        this.container.addChild(title);
        
        // 副标题
        const subtitle = new Laya.Text();
        subtitle.text = "按住蓄力 · 松开跳跃";
        subtitle.font = "Arial";
        subtitle.fontSize = 30;
        subtitle.color = "#CCCCCC";
        subtitle.x = Laya.stage.width / 2 - 120;
        subtitle.y = 420;
        this.container.addChild(subtitle);
        
        // 开始按钮
        const startBtn = new Laya.Sprite();
        startBtn.graphics.drawRect(0, 0, 200, 60, "#4CAF50");
        startBtn.graphics.drawRoundRect(0, 0, 200, 60, 10, 10, "#4CAF50");
        startBtn.x = Laya.stage.width / 2 - 100;
        startBtn.y = 550;
        startBtn.on(Laya.Event.MOUSE_DOWN, this, this.onClick);
        this.container.addChild(startBtn);
        
        // 按钮文字
        const btnText = new Laya.Text();
        btnText.text = "开始游戏";
        btnText.font = "Arial Black";
        btnText.fontSize = 30;
        btnText.color = "#FFFFFF";
        btnText.bold = true;
        btnText.x = startBtn.x + 35;
        btnText.y = startBtn.y + 15;
        this.container.addChild(btnText);
        
        // 说明文字
        const tips = new Laya.Text();
        tips.text = "💡 按住时间越长，跳得越远\n🎯 落在方块中心可得额外分数\n🏆 挑战最高分！";
        tips.font = "Arial";
        tips.fontSize = 24;
        tips.color = "#AAAAAA";
        tips.x = Laya.stage.width / 2 - 150;
        tips.y = 680;
        tips.lineSpacing = 10;
        this.container.addChild(tips);
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

    onClick(e) {
        e.stopPropagation();
        if (this.onStart) {
            this.onStart();
        }
    }

    destroy() {
        if (this.container && this.container.parent) {
            this.container.parent.removeChild(this.container);
        }
    }
}
