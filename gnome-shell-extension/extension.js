const { GObject, St } = imports.gi

const Main = imports.ui.main
const PanelMenu = imports.ui.panelMenu
const PopupMenu = imports.ui.popupMenu
const Soup = imports.gi.Soup
const Mainloop = imports.mainloop

const POLL_INTERVAL_SEC = 20
const BASE_URL = 'http://192.168.1.200:8080/light'
const SOUP_SESSION = new Soup.Session()
const LIGHTS = ['Ufficio', 'Scale', 'Bagno', 'Camera', 'Armadio']

function setLight(light, value) {
  return new Promise((resolve, reject) => {
    let args = ''
    if (value !== undefined && light !== undefined) {
      args = '?light=' + light + '&on=' + value
    }
    const message = Soup.Message.new('GET', BASE_URL + args)
    SOUP_SESSION.queue_message(message, () => {
      if (message.status_code === Soup.KnownStatusCode.OK) {
        resolve(JSON.parse(message.response_body.data))
      } else {
        reject('!= 200 response code')
      }
    })
  })
}

const Indicator = GObject.registerClass(
  class Indicator extends PanelMenu.Button {
    _init() {
      super._init(0.0, 'Home automation')

      this.add_child(
        new St.Icon({
          icon_name: 'dialog-information-symbolic',
          style_class: 'system-status-icon',
        })
      )

      // high order functions to set the light state
      const updateLight = (light) => (params) =>
        setLight(light, params.state)
          .then((state) => this.setLightState(state))
          .catch(console.error)

      // create all the menu entries, with a for loop
      for (const light of LIGHTS) {
        const key = light.toLowerCase()
        this[key] = new PopupMenu.PopupSwitchMenuItem(light, false)
        this[key].connect('activate', updateLight(key))
        this.menu.addMenuItem(this[key])
      }

      // prevent menu close
      this.menu.itemActivated = () => {}
    }

    setLightState(state) {
      for (const light of LIGHTS) {
        this[light.toLowerCase()].setToggleState(state[light.toLowerCase()].state === 1)
      }
    }
  }
)

class Extension {
  constructor(uuid) {
    this._uuid = uuid
    this.timeout = null
  }

  enable() {
    this._indicator = new Indicator()
    Main.panel.addToStatusArea(this._uuid, this._indicator)

    // get current state
    setLight()
      .then((state) => this._indicator.setLightState(state))
      .catch(console.error)

    this.timeout = Mainloop.timeout_add_seconds(POLL_INTERVAL_SEC, () => {
      // get current state
      setLight()
        .then((state) => this._indicator.setLightState(state))
        .catch(console.error)

      // by returning true the timeout is not canceled
      return true
    })
  }

  disable() {
    this._indicator.destroy()
    this._indicator = null
    if (this.timeout != null) {
      Mainloop.source_remove(this.timeout);
    }
    this.timeout = null
  }
}

function init(meta) {
  return new Extension(meta.uuid)
}
